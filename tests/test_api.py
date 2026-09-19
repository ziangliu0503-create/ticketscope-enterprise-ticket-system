from pathlib import Path

import pytest

from backend.app import create_app
from backend.seed import seed_database


@pytest.fixture()
def client(tmp_path: Path):
    database = tmp_path / "test.db"
    seed_database(str(database), count=30, seed=7)
    app = create_app({"TESTING": True, "DATABASE": str(database)})
    with app.test_client() as test_client:
        yield test_client


def test_health_and_meta(client):
    assert client.get("/api/health").get_json()["status"] == "ok"
    meta = client.get("/api/meta").get_json()
    assert "账号权限" in meta["categories"]
    assert any(user["role"] == "agent" for user in meta["users"])


def test_list_and_filter_tickets(client):
    response = client.get("/api/tickets?per_page=10")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["total"] == 30
    assert len(payload["items"]) == 10
    filtered = client.get("/api/tickets?status=NEW&per_page=100").get_json()
    assert all(item["status"] == "NEW" for item in filtered["items"])


def test_create_and_transition_ticket(client):
    meta = client.get("/api/meta").get_json()
    requester = next(user for user in meta["users"] if user["role"] == "requester")
    agent = next(user for user in meta["users"] if user["role"] == "agent")
    created = client.post("/api/tickets", json={
        "title": "测试数据导入失败",
        "description": "导入CSV时报字段格式错误",
        "department": "供应链部",
        "category": "数据问题",
        "priority": "HIGH",
        "requester_id": requester["id"],
    })
    assert created.status_code == 201
    ticket = created.get_json()
    assert ticket["status"] == "NEW"

    assigned = client.post(f"/api/tickets/{ticket['id']}/transition", json={
        "status": "ASSIGNED",
        "assignee_id": agent["id"],
        "operator_id": agent["id"],
    })
    assert assigned.status_code == 200
    assert assigned.get_json()["assignee_id"] == agent["id"]

    client.post(f"/api/tickets/{ticket['id']}/transition", json={
        "status": "IN_PROGRESS", "operator_id": agent["id"]
    })
    resolved = client.post(f"/api/tickets/{ticket['id']}/transition", json={
        "status": "RESOLVED",
        "operator_id": agent["id"],
        "resolution": "修正CSV日期字段后重新导入成功",
    })
    assert resolved.status_code == 200
    assert resolved.get_json()["resolved_at"] is not None


def test_invalid_transition_is_rejected(client):
    new_ticket = client.get("/api/tickets?status=NEW&per_page=1").get_json()["items"][0]
    response = client.post(f"/api/tickets/{new_ticket['id']}/transition", json={"status": "CLOSED"})
    assert response.status_code == 400


def test_dashboard_reconciles_total(client):
    dashboard = client.get("/api/dashboard").get_json()
    assert dashboard["summary"]["total"] == 30
    assert sum(item["value"] for item in dashboard["by_status"]) == 30
    assert len(dashboard["trend"]) == 30


def test_built_frontend_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "企业工单管理系统" in response.get_data(as_text=True)
