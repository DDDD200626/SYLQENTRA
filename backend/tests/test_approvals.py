from tests.conftest import auth_header, register


def test_email_tool_waits_for_an_admin_decision(client, fake_models):
    owner = register(client, "approve@example.com", "Approve Co")
    headers = auth_header(owner["access_token"])
    run = client.post(
        "/api/v1/agents/automation/run",
        headers=headers,
        json={"task_input": "보고서를 이메일로 보내줘", "provider": "openai", "model": "gpt-test", "tool": "email"},
    )
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "awaiting_approval"
    assert run.json()["prompt_tokens"] == 0

    listed = client.get("/api/v1/approvals", headers=headers)
    approval_id = listed.json()[0]["id"]
    decided = client.post(f"/api/v1/approvals/{approval_id}/decide", headers=headers, json={"decision": "approved"})
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"
