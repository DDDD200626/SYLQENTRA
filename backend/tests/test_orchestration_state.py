import pytest

from app.orchestration.state import OrchestrationState
from tests.conftest import auth_header, register


def test_request_moves_through_the_execution_states():
    state = OrchestrationState(request="이번 달 매출 보고서를 작성해줘")
    assert state.status == "pending"
    state.transition("planning")
    state.plan = ["data", "document"]
    state.transition("running")
    state.outputs["data"] = "매출 100"
    state.transition("reviewing")
    state.transition("completed")
    assert state.status == "completed"
    assert state.plan == ["data", "document"]


def test_orchestration_runs_the_planned_agents(client, fake_models):
    owner = register(client, "orch@example.com", "Orchestration Company")
    response = client.post(
        "/api/v1/orchestrations",
        headers=auth_header(owner["access_token"]),
        json={"request": "이번 달 매출 보고서를 작성해줘", "provider": "openai", "model": "gpt-test"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert "data" in body["plan"]
    assert "document" in body["plan"]
    assert "Review Agent" in body["final_output"]
    assert body["outputs"]["data"]


def test_completed_request_cannot_run_again():
    state = OrchestrationState(request="완료된 업무")
    for status in ("planning", "running", "reviewing", "completed"):
        state.transition(status)
    with pytest.raises(ValueError):
        state.transition("running")