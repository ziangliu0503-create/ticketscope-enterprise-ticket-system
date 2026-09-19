from pathlib import Path

import pytest
from openpyxl import load_workbook

from backend.app import create_app
from backend.seed import seed_database


@pytest.fixture()
def client(tmp_path: Path):
    database = tmp_path / "test.db"
    seed_database(str(database), count=30, seed=7)
    app = create_app({"TESTING": True, "DATABASE": str(database), "SECRET_KEY": "test-secret"})
    with app.test_client() as test_client:
        yield test_client


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "Demo123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


@pytest.fixture()
def admin_headers(client):
    return login(client, "ziang.liu@example.com")


@pytest.fixture()
def agent_headers(client):
    return login(client, "wang.chen@example.com")


@pytest.fixture()
def requester_headers(client):
    return login(client, "user1@example.com")


def test_health_is_public_and_meta_requires_login(client, admin_headers):
    assert client.get("/api/health").get_json()["status"] == "ok"
    assert client.get("/api/meta").status_code == 401
    meta = client.get("/api/meta", headers=admin_headers).get_json()
    assert meta["current_user"]["role"] == "admin"
    assert meta["sla_hours"]["URGENT"] == 8


def test_role_based_ticket_visibility(client, admin_headers, requester_headers):
    admin_total = client.get("/api/tickets?per_page=100", headers=admin_headers).get_json()["total"]
    requester_payload = client.get("/api/tickets?per_page=100", headers=requester_headers).get_json()
    assert admin_total == 30
    assert requester_payload["total"] < admin_total
    assert all(item["requester_email"] == "user1@example.com" for item in requester_payload["items"])


def test_requester_can_create_but_cannot_assign(client, requester_headers):
    created = client.post("/api/tickets", headers=requester_headers, json={
        "title": "测试数据导入失败",
        "description": "导入CSV时报字段格式错误",
        "department": "财务部",
        "category": "数据问题",
        "priority": "HIGH",
    })
    assert created.status_code == 201
    ticket = created.get_json()
    forbidden = client.post(
        f"/api/tickets/{ticket['id']}/transition",
        headers=requester_headers,
        json={"status": "ASSIGNED"},
    )
    assert forbidden.status_code == 403


def test_admin_full_transition_flow(client, admin_headers):
    meta = client.get("/api/meta", headers=admin_headers).get_json()
    requester = next(user for user in meta["users"] if user["role"] == "requester")
    agent = next(user for user in meta["users"] if user["role"] == "agent")
    created = client.post("/api/tickets", headers=admin_headers, json={
        "title": "测试数据导入失败",
        "description": "导入CSV时报字段格式错误",
        "department": requester["department"],
        "category": "数据问题",
        "priority": "HIGH",
        "requester_id": requester["id"],
    })
    ticket = created.get_json()
    assigned = client.post(f"/api/tickets/{ticket['id']}/transition", headers=admin_headers, json={
        "status": "ASSIGNED", "assignee_id": agent["id"], "note": "分配处理",
    })
    assert assigned.status_code == 200
    client.post(f"/api/tickets/{ticket['id']}/transition", headers=admin_headers, json={"status": "IN_PROGRESS"})
    resolved = client.post(f"/api/tickets/{ticket['id']}/transition", headers=admin_headers, json={
        "status": "RESOLVED", "resolution": "修正CSV日期字段后重新导入成功",
    })
    assert resolved.status_code == 200
    assert resolved.get_json()["resolved_at"] is not None
    closed = client.post(f"/api/tickets/{ticket['id']}/transition", headers=admin_headers, json={"status": "CLOSED"})
    assert closed.get_json()["status"] == "CLOSED"


def test_invalid_transition_is_rejected(client, admin_headers):
    new_ticket = client.get("/api/tickets?status=NEW&per_page=1", headers=admin_headers).get_json()["items"][0]
    response = client.post(f"/api/tickets/{new_ticket['id']}/transition", headers=admin_headers, json={"status": "CLOSED"})
    assert response.status_code == 403


def test_dashboard_and_sla_filter(client, admin_headers):
    dashboard = client.get("/api/dashboard", headers=admin_headers).get_json()
    assert dashboard["summary"]["total"] == 30
    assert sum(item["value"] for item in dashboard["by_status"]) == 30
    assert "sla_compliance_rate" in dashboard["summary"]
    overdue = client.get("/api/tickets?sla=OVERDUE&per_page=100", headers=admin_headers).get_json()
    assert all(item["sla_status"] == "OVERDUE" for item in overdue["items"])


def test_csv_and_excel_export(client, admin_headers, tmp_path):
    csv_response = client.get("/api/reports/tickets.csv?status=NEW", headers=admin_headers)
    assert csv_response.status_code == 200
    assert csv_response.data.startswith(b"\xef\xbb\xbf")
    xlsx_response = client.get("/api/reports/tickets.xlsx", headers=admin_headers)
    assert xlsx_response.status_code == 200
    output = tmp_path / "report.xlsx"
    output.write_bytes(xlsx_response.data)
    workbook = load_workbook(output, read_only=True)
    assert workbook["工单明细"]["A1"].value == "工单编号"


def test_only_admin_can_export_reports(client, agent_headers, requester_headers):
    assert client.get("/api/reports/tickets.csv", headers=agent_headers).status_code == 403
    assert client.get("/api/reports/tickets.xlsx", headers=requester_headers).status_code == 403


def test_built_frontend_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "企业工单管理系统" in response.get_data(as_text=True)
