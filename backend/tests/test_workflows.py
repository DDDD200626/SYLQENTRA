from datetime import datetime, timezone

from app.services.workflow_service import cron_is_due
from tests.conftest import auth_header, register


def test_cron_matches_wildcards():
    now = datetime(2026, 11, 23, 9, 0, tzinfo=timezone.utc)
    assert cron_is_due("0 9 * * *", now) is True
    assert cron_is_due("15 9 * * *", now) is False
    assert cron_is_due("manual", now) is False


def test_workflow_executes_nodes_in_edge_order(client, fake_models):
    owner = register(client, "flow@example.com", "Flow Co")
    headers = auth_header(owner["access_token"])
    created = client.post(
        "/api/v1/workflows",
        headers=headers,
        json={
            "name": "월간 매출",
            "description": "매출 보고서를 만든다",
            "schedule_cron": "0 9 * * *",
            "nodes": [
                {"node_key": "analyze", "node_type": "agent", "config": {"role": "data"}},
                {"node_key": "write", "node_type": "agent", "config": {"role": "document"}},
            ],
            "edges": [{"source": "analyze", "target": "write"}],
        },
    )
    assert created.status_code == 201, created.text
    executed = client.post(
        f"/api/v1/workflows/{created.json()['id']}/execute",
        headers=headers,
        json={"provider": "openai", "model": "gpt-test", "task_input": "1월 100, 2월 130"},
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    listed = client.get("/api/v1/workflows", headers=headers)
    assert listed.json()[0]["name"] == "월간 매출"
    detail = client.get(f"/api/v1/workflows/{created.json()['id']}", headers=headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert [node["config"]["role"] for node in body["nodes"]] == ["data", "document"]
    assert body["edges"] == [{"source": "analyze", "target": "write"}]
