import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from .db import get_db, init_app as init_db_app, init_db


STATUSES = ["NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"]
DEPARTMENTS = ["财务部", "供应链部", "市场部", "销售部", "人力资源部", "生产运营部"]
CATEGORIES = ["账号权限", "网络连接", "软件故障", "数据问题", "设备故障", "系统咨询"]
SLA_HOURS = {"LOW": 72, "MEDIUM": 48, "HIGH": 24, "URGENT": 8}

ALLOWED_TRANSITIONS = {
    "NEW": {"ASSIGNED"},
    "ASSIGNED": {"IN_PROGRESS"},
    "IN_PROGRESS": {"RESOLVED"},
    "RESOLVED": {"CLOSED", "IN_PROGRESS"},
    "CLOSED": {"IN_PROGRESS"},
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def row_to_dict(row):
    return dict(row) if row is not None else None


def fetch_ticket(ticket_id):
    return get_db().execute(
        """
        SELECT t.*, requester.name AS requester_name, assignee.name AS assignee_name
        FROM tickets t
        JOIN users requester ON requester.id = t.requester_id
        LEFT JOIN users assignee ON assignee.id = t.assignee_id
        WHERE t.id = ?
        """,
        (ticket_id,),
    ).fetchone()


def error(message, status=400, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


def create_app(test_config=None):
    frontend_dist = Path(__file__).parents[1] / "frontend" / "dist"
    app = Flask(
        __name__,
        static_folder=str(frontend_dist) if frontend_dist.exists() else None,
        static_url_path="",
    )
    default_database = Path(__file__).with_name("data") / "tickets.db"
    app.config.from_mapping(
        DATABASE=os.environ.get("TICKET_DATABASE", str(default_database)),
        JSON_AS_ASCII=False,
    )
    if test_config:
        app.config.update(test_config)
    CORS(app)
    init_db_app(app)

    with app.app_context():
        init_db()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "enterprise-ticket-api"})

    @app.get("/api/meta")
    def meta():
        users = [row_to_dict(row) for row in get_db().execute(
            "SELECT id, name, email, department, role FROM users ORDER BY role, name"
        ).fetchall()]
        return jsonify({
            "statuses": STATUSES,
            "priorities": PRIORITIES,
            "departments": DEPARTMENTS,
            "categories": CATEGORIES,
            "users": users,
        })

    @app.get("/api/tickets")
    def list_tickets():
        page = max(1, request.args.get("page", default=1, type=int))
        per_page = min(100, max(1, request.args.get("per_page", default=20, type=int)))
        conditions = []
        parameters = []
        for field in ("status", "priority", "department", "category"):
            value = request.args.get(field)
            if value:
                conditions.append(f"t.{field} = ?")
                parameters.append(value)
        search = request.args.get("search", "").strip()
        if search:
            conditions.append("(t.ticket_no LIKE ? OR t.title LIKE ? OR t.description LIKE ?)")
            token = f"%{search}%"
            parameters.extend([token, token, token])
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        db = get_db()
        total = db.execute(f"SELECT COUNT(*) AS count FROM tickets t{where}", parameters).fetchone()["count"]
        rows = db.execute(
            f"""
            SELECT t.*, requester.name AS requester_name, assignee.name AS assignee_name
            FROM tickets t
            JOIN users requester ON requester.id = t.requester_id
            LEFT JOIN users assignee ON assignee.id = t.assignee_id
            {where}
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
            """,
            [*parameters, per_page, (page - 1) * per_page],
        ).fetchall()
        return jsonify({"items": [row_to_dict(row) for row in rows], "page": page, "per_page": per_page, "total": total})

    @app.get("/api/tickets/<int:ticket_id>")
    def get_ticket(ticket_id):
        ticket = fetch_ticket(ticket_id)
        if ticket is None:
            return error("工单不存在", 404)
        logs = get_db().execute(
            """
            SELECT l.*, u.name AS operator_name
            FROM ticket_logs l LEFT JOIN users u ON u.id = l.operator_id
            WHERE l.ticket_id = ? ORDER BY l.created_at DESC
            """,
            (ticket_id,),
        ).fetchall()
        return jsonify({"ticket": row_to_dict(ticket), "logs": [row_to_dict(row) for row in logs]})

    @app.post("/api/tickets")
    def create_ticket():
        payload = request.get_json(silent=True) or {}
        required = ["title", "description", "department", "category", "priority", "requester_id"]
        missing = [field for field in required if payload.get(field) in (None, "")]
        if missing:
            return error("缺少必填字段", details=missing)
        if payload["priority"] not in PRIORITIES or payload["department"] not in DEPARTMENTS or payload["category"] not in CATEGORIES:
            return error("提交的数据包含无效选项")
        db = get_db()
        requester = db.execute("SELECT id FROM users WHERE id = ?", (payload["requester_id"],)).fetchone()
        if requester is None:
            return error("提交人不存在")
        now = utc_now()
        due_at = now + timedelta(hours=SLA_HOURS[payload["priority"]])
        year_month = now.strftime("%Y%m")
        existing_numbers = db.execute(
            "SELECT ticket_no FROM tickets WHERE ticket_no LIKE ?", (f"TKT-{year_month}-%",)
        ).fetchall()
        next_number = max((int(row["ticket_no"].rsplit("-", 1)[-1]) for row in existing_numbers), default=0) + 1
        ticket_no = f"TKT-{year_month}-{next_number:04d}"
        try:
            cursor = db.execute(
                """
                INSERT INTO tickets (
                    ticket_no, title, description, department, category, priority, status,
                    requester_id, assignee_id, created_at, updated_at, due_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'NEW', ?, NULL, ?, ?, ?)
                """,
                (ticket_no, payload["title"].strip(), payload["description"].strip(), payload["department"],
                 payload["category"], payload["priority"], payload["requester_id"], iso(now), iso(now), iso(due_at)),
            )
            ticket_id = cursor.lastrowid
            db.execute(
                """
                INSERT INTO ticket_logs (ticket_id, action, from_status, to_status, operator_id, note, created_at)
                VALUES (?, 'CREATED', NULL, 'NEW', ?, ?, ?)
                """,
                (ticket_id, payload["requester_id"], payload.get("note", "工单已创建"), iso(now)),
            )
            db.commit()
        except sqlite3.IntegrityError as exc:
            return error("工单创建失败", details=[str(exc)])
        return jsonify(row_to_dict(fetch_ticket(ticket_id))), 201

    @app.patch("/api/tickets/<int:ticket_id>")
    def update_ticket(ticket_id):
        ticket = fetch_ticket(ticket_id)
        if ticket is None:
            return error("工单不存在", 404)
        payload = request.get_json(silent=True) or {}
        editable = {"title", "description", "department", "category", "priority", "assignee_id", "resolution"}
        updates = {key: value for key, value in payload.items() if key in editable}
        if not updates:
            return error("没有可更新的字段")
        if "priority" in updates and updates["priority"] not in PRIORITIES:
            return error("优先级无效")
        if "department" in updates and updates["department"] not in DEPARTMENTS:
            return error("部门无效")
        if "category" in updates and updates["category"] not in CATEGORIES:
            return error("问题类型无效")
        if "assignee_id" in updates and updates["assignee_id"] is not None:
            agent = get_db().execute("SELECT id FROM users WHERE id = ? AND role IN ('agent', 'admin')", (updates["assignee_id"],)).fetchone()
            if agent is None:
                return error("负责人必须是技术人员或管理员")
        updates["updated_at"] = iso(utc_now())
        assignments = ", ".join(f"{key} = ?" for key in updates)
        get_db().execute(f"UPDATE tickets SET {assignments} WHERE id = ?", [*updates.values(), ticket_id])
        operator_id = payload.get("operator_id")
        get_db().execute(
            """
            INSERT INTO ticket_logs (ticket_id, action, operator_id, note, created_at)
            VALUES (?, 'UPDATED', ?, ?, ?)
            """,
            (ticket_id, operator_id, payload.get("note", "更新工单信息"), updates["updated_at"]),
        )
        get_db().commit()
        return jsonify(row_to_dict(fetch_ticket(ticket_id)))

    @app.post("/api/tickets/<int:ticket_id>/transition")
    def transition_ticket(ticket_id):
        ticket = fetch_ticket(ticket_id)
        if ticket is None:
            return error("工单不存在", 404)
        payload = request.get_json(silent=True) or {}
        target = payload.get("status")
        if target not in ALLOWED_TRANSITIONS.get(ticket["status"], set()):
            return error(f"不允许从 {ticket['status']} 变更为 {target}")
        assignee_id = payload.get("assignee_id", ticket["assignee_id"])
        if target in {"ASSIGNED", "IN_PROGRESS", "RESOLVED"} and not assignee_id:
            return error("进入处理流程前必须分配负责人")
        resolution = payload.get("resolution", ticket["resolution"])
        if target == "RESOLVED" and not str(resolution or "").strip():
            return error("解决工单时必须填写解决方案")
        now = utc_now()
        if target == "RESOLVED":
            resolved_at = iso(now)
        elif target == "CLOSED":
            resolved_at = ticket["resolved_at"] or iso(now)
        else:
            resolved_at = None
        db = get_db()
        db.execute(
            """
            UPDATE tickets SET status = ?, assignee_id = ?, resolution = ?, resolved_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (target, assignee_id, resolution, resolved_at, iso(now), ticket_id),
        )
        db.execute(
            """
            INSERT INTO ticket_logs (ticket_id, action, from_status, to_status, operator_id, note, created_at)
            VALUES (?, 'STATUS_CHANGED', ?, ?, ?, ?, ?)
            """,
            (ticket_id, ticket["status"], target, payload.get("operator_id"), payload.get("note", "状态已更新"), iso(now)),
        )
        db.commit()
        return jsonify(row_to_dict(fetch_ticket(ticket_id)))

    @app.get("/api/dashboard")
    def dashboard():
        db = get_db()
        now = utc_now()
        summary = row_to_dict(db.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved,
                SUM(CASE WHEN status NOT IN ('RESOLVED', 'CLOSED') AND due_at < ? THEN 1 ELSE 0 END) AS overdue
            FROM tickets
            """,
            (iso(now),),
        ).fetchone())
        resolution_rows = db.execute(
            "SELECT created_at, resolved_at FROM tickets WHERE resolved_at IS NOT NULL"
        ).fetchall()
        durations = [(parse_iso(row["resolved_at"]) - parse_iso(row["created_at"])).total_seconds() / 3600 for row in resolution_rows]
        summary["resolution_rate"] = round((summary["resolved"] / summary["total"] * 100), 1) if summary["total"] else 0
        summary["avg_resolution_hours"] = round(sum(durations) / len(durations), 1) if durations else 0

        def grouped(column):
            return [row_to_dict(row) for row in db.execute(
                f"SELECT {column} AS name, COUNT(*) AS value FROM tickets GROUP BY {column} ORDER BY value DESC"
            ).fetchall()]

        since = iso(now - timedelta(days=29))
        created_by_day = {
            row["day"]: row["value"] for row in db.execute(
                "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS value FROM tickets WHERE created_at >= ? GROUP BY day",
                (since,),
            ).fetchall()
        }
        resolved_by_day = {
            row["day"]: row["value"] for row in db.execute(
                "SELECT substr(resolved_at, 1, 10) AS day, COUNT(*) AS value FROM tickets WHERE resolved_at >= ? GROUP BY day",
                (since,),
            ).fetchall()
        }
        trend = []
        for offset in range(29, -1, -1):
            day = (now - timedelta(days=offset)).strftime("%Y-%m-%d")
            trend.append({"day": day, "created": created_by_day.get(day, 0), "resolved": resolved_by_day.get(day, 0)})
        return jsonify({
            "summary": summary,
            "by_status": grouped("status"),
            "by_priority": grouped("priority"),
            "by_category": grouped("category"),
            "by_department": grouped("department"),
            "trend": trend,
            "generated_at": iso(now),
        })

    if frontend_dist.exists():
        @app.get("/")
        def frontend_index():
            return send_from_directory(frontend_dist, "index.html")

        @app.get("/<path:asset_path>")
        def frontend_assets(asset_path):
            target = frontend_dist / asset_path
            if target.is_file():
                return send_from_directory(frontend_dist, asset_path)
            return send_from_directory(frontend_dist, "index.html")

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
