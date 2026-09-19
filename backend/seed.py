import argparse
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEPARTMENTS = ["财务部", "供应链部", "市场部", "销售部", "人力资源部", "生产运营部"]
CATEGORIES = ["账号权限", "网络连接", "软件故障", "数据问题", "设备故障", "系统咨询"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"]
STATUSES = ["NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"]

TITLES = {
    "账号权限": ["无法登录业务系统", "账号权限申请", "共享目录无访问权限", "密码重置失败"],
    "网络连接": ["办公网络频繁断开", "VPN无法连接", "会议室网络延迟", "无线网络无法认证"],
    "软件故障": ["客户端启动报错", "办公软件无法保存", "系统页面加载异常", "插件安装失败"],
    "数据问题": ["报表数据未更新", "批量导入失败", "字段映射错误", "历史数据重复"],
    "设备故障": ["打印机无法使用", "显示器无信号", "笔记本运行缓慢", "扫码设备离线"],
    "系统咨询": ["咨询审批流程配置", "咨询报表导出方式", "新员工系统使用咨询", "移动端功能咨询"],
}

SLA_HOURS = {"LOW": 72, "MEDIUM": 48, "HIGH": 24, "URGENT": 8}


def iso(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def seed_database(database_path: str, count: int = 220, seed: int = 20260918):
    random.seed(seed)
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(schema)
    connection.execute("DELETE FROM ticket_logs")
    connection.execute("DELETE FROM tickets")
    connection.execute("DELETE FROM users")

    now = datetime.now(timezone.utc)
    users = [
        ("刘子昂", "ziang.liu@example.com", "信息技术部", "admin"),
        ("王晨", "wang.chen@example.com", "信息技术部", "agent"),
        ("李明", "li.ming@example.com", "信息技术部", "agent"),
        ("陈雪", "chen.xue@example.com", "信息技术部", "agent"),
    ]
    for index, department in enumerate(DEPARTMENTS, start=1):
        users.append((f"业务用户{index}", f"user{index}@example.com", department, "requester"))
    connection.executemany(
        "INSERT INTO users (name, email, department, role, created_at) VALUES (?, ?, ?, ?, ?)",
        [(name, email, department, role, iso(now - timedelta(days=120))) for name, email, department, role in users],
    )
    user_rows = connection.execute("SELECT id, role, department FROM users").fetchall()
    requester_ids = [row["id"] for row in user_rows if row["role"] == "requester"]
    agent_ids = [row["id"] for row in user_rows if row["role"] in ("agent", "admin")]

    status_weights = [0.12, 0.14, 0.22, 0.26, 0.26]
    priority_weights = [0.17, 0.48, 0.27, 0.08]
    for index in range(1, count + 1):
        created = now - timedelta(days=random.randint(0, 89), hours=random.randint(0, 20), minutes=random.randint(0, 59))
        category = random.choice(CATEGORIES)
        priority = random.choices(PRIORITIES, weights=priority_weights, k=1)[0]
        status = random.choices(STATUSES, weights=status_weights, k=1)[0]
        department = random.choice(DEPARTMENTS)
        requester = random.choice(requester_ids)
        assignee = None if status == "NEW" else random.choice(agent_ids)
        due_at = created + timedelta(hours=SLA_HOURS[priority])
        updated = min(created + timedelta(hours=random.randint(1, max(2, SLA_HOURS[priority] + 36))), now)
        status_index = STATUSES.index(status)
        total_hours = max(1, (updated - created).total_seconds() / 3600)
        step_hours = total_hours / max(1, status_index)
        transition_times = {
            STATUSES[step]: min(created + timedelta(hours=step_hours * step), now)
            for step in range(1, status_index + 1)
        }
        resolved_at = None
        resolution = None
        if status in ("RESOLVED", "CLOSED"):
            resolved_at = transition_times["RESOLVED"]
            resolution = random.choice([
                "完成账号配置并通知提交人验证。",
                "调整系统配置后恢复正常，已记录处理步骤。",
                "修正数据格式并重新执行导入任务。",
                "完成设备检查及驱动更新，问题已解决。",
            ])
        title = random.choice(TITLES[category])
        description = f"{department}反馈：{title}。请协助定位原因并记录处理结果。"
        cursor = connection.execute(
            """
            INSERT INTO tickets (
                ticket_no, title, description, department, category, priority, status,
                requester_id, assignee_id, created_at, updated_at, due_at, resolved_at, resolution
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"TKT-{created:%Y%m}-{index:04d}", title, description, department, category,
                priority, status, requester, assignee, iso(created), iso(updated), iso(due_at),
                iso(resolved_at) if resolved_at else None, resolution,
            ),
        )
        ticket_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO ticket_logs (ticket_id, action, from_status, to_status, operator_id, note, created_at)
            VALUES (?, 'CREATED', NULL, 'NEW', ?, '模拟数据：工单已创建', ?)
            """,
            (ticket_id, requester, iso(created)),
        )
        for step in range(1, status_index + 1):
            from_status = STATUSES[step - 1]
            to_status = STATUSES[step]
            connection.execute(
                """
                INSERT INTO ticket_logs (ticket_id, action, from_status, to_status, operator_id, note, created_at)
                VALUES (?, 'STATUS_CHANGED', 'NEW', ?, ?, '模拟状态流转记录', ?)
                """,
                (ticket_id, to_status, assignee, iso(transition_times[to_status])),
            )

    connection.commit()
    connection.close()
    return count


def main():
    parser = argparse.ArgumentParser(description="Create deterministic simulated ticket data.")
    parser.add_argument("--database", default=str(Path(__file__).with_name("data") / "tickets.db"))
    parser.add_argument("--count", type=int, default=220)
    args = parser.parse_args()
    created = seed_database(args.database, args.count)
    print(f"Created {created} simulated tickets in {args.database}")


if __name__ == "__main__":
    main()
