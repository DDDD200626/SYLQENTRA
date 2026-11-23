import json

import httpx

from app.integrations.github.github_connector import GitHubConnector
from tests.conftest import auth_header, register


def test_sales_report_orchestration_scenario(client, fake_models):
    owner = register(client, "sales@example.com", "Sales Co")
    headers = auth_header(owner["access_token"])
    response = client.post(
        "/api/v1/orchestrations",
        headers=headers,
        json={"request": "이번 달 매출 데이터를 분석하고 보고서를 작성해줘", "provider": "openai", "model": "gpt-test"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "completed"
    assert "data" in response.json()["plan"]
    assert "document" in response.json()["plan"]


def test_internal_document_search_scenario(client, fake_models):
    owner = register(client, "docs@example.com", "Docs Co")
    headers = auth_header(owner["access_token"])
    uploaded = client.post(
        "/api/v1/knowledge/documents",
        headers=headers,
        json={"title": "규정", "filename": "policy.md", "content": "외부 이메일은 관리자 승인이 필요합니다."},
    )
    assert uploaded.status_code == 201
    answer = client.post(
        "/api/v1/knowledge/ask",
        headers=headers,
        json={"query": "외부 이메일 승인", "provider": "openai", "model": "gpt-test"},
    )
    assert "승인" in answer.json()["answer"]
    assert answer.json()["sources"]


def test_developer_issue_review_scenario():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"number": 12, "title": "보고서 계산 오류", "state": "open"}])

    github = GitHubConnector("token", transport=httpx.MockTransport(handler))
    issues = github.list_issues("acme", "billing")
    github.close()
    assert issues[0]["title"] == "보고서 계산 오류"
    assert json.dumps(issues, ensure_ascii=False)
