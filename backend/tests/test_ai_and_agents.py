import pytest

from app.agents.registry import AGENT_CLASSES, create_agent
from app.ai_models.base_provider import AIResponse, BaseProvider
from app.ai_models.model_manager import ModelManager, get_model_manager
from app.main import app
from tests.conftest import auth_header, register


class EchoProvider(BaseProvider):
    def __init__(self, name: str) -> None:
        self.name = name

    def generate(self, *, model: str, prompt: str, system_prompt: str | None = None) -> AIResponse:
        return AIResponse(
            text=system_prompt or prompt,
            prompt_tokens=2,
            completion_tokens=3,
            latency_ms=4,
            model_name=model,
            provider=self.name,
        )


def _manager() -> ModelManager:
    return ModelManager(
        providers={
            "openai": EchoProvider("openai"),
            "anthropic": EchoProvider("anthropic"),
            "google": EchoProvider("google"),
        }
    )


@pytest.fixture
def fake_models():
    app.dependency_overrides[get_model_manager] = _manager
    yield
    app.dependency_overrides.pop(get_model_manager, None)


def test_each_agent_has_a_distinct_contract():
    prompts = {role: agent.system_prompt for role, agent in AGENT_CLASSES.items()}
    assert len(prompts) == 7
    assert len(set(prompts.values())) == 7
    manager = _manager()
    blocked = create_agent("automation", manager, "openai", "gpt-test").run("메일 보내줘", tool="database_write")
    assert blocked.status == "blocked"
    assert blocked.prompt_tokens == 0
    allowed = create_agent("data", manager, "google", "gemini-test").run("1월 100, 2월 120")
    assert allowed.status == "completed"
    assert "Data Agent" in allowed.output
    assert allowed.provider == "google"


def test_generate_records_usage_and_enforces_the_monthly_limit(client, fake_models):
    owner = register(client, "owner@example.com", "Acme")
    headers = auth_header(owner["access_token"])

    created = client.post(
        "/api/v1/ai/generate",
        headers=headers,
        json={"provider": "openai", "model": "gpt-test", "prompt": "매출을 요약해줘"},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["text"] == "매출을 요약해줘"
    assert body["prompt_tokens"] == 2
    assert body["completion_tokens"] == 3

    usage = client.get("/api/v1/ai/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["tokens_used"] == 5
    assert usage.json()["monthly_token_limit"] == 100000

    limited = client.put("/api/v1/ai/usage-limit", headers=headers, json={"monthly_token_limit": 5})
    assert limited.status_code == 200
    blocked = client.post(
        "/api/v1/ai/generate",
        headers=headers,
        json={"provider": "openai", "model": "gpt-test", "prompt": "한 번 더"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "USAGE_LIMIT_EXCEEDED"


def test_agent_run_is_tenant_scoped_and_blocks_unknown_tools(client, fake_models):
    owner = register(client, "owner@example.com", "Acme")
    headers = auth_header(owner["access_token"])
    viewer = client.post(
        "/api/v1/organizations/members",
        headers=headers,
        json={
            "email": "viewer@example.com",
            "full_name": "Viewer",
            "password": "Viewer1234",
            "role": "viewer",
        },
    )
    assert viewer.status_code == 201

    run = client.post(
        "/api/v1/agents/research/run",
        headers=headers,
        json={"task_input": "사내 매출 메모를 요약해줘", "provider": "anthropic", "model": "claude-test"},
    )
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "completed"
    assert "Research Agent" in run.json()["output"]
    assert run.json()["provider"] == "anthropic"

    denied_tool = client.post(
        "/api/v1/agents/automation/run",
        headers=headers,
        json={
            "task_input": "데이터베이스를 수정해줘",
            "provider": "openai",
            "model": "gpt-test",
            "tool": "database_write",
        },
    )
    assert denied_tool.status_code == 200
    assert denied_tool.json()["status"] == "blocked"
    assert denied_tool.json()["prompt_tokens"] == 0

    viewer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@example.com", "password": "Viewer1234"},
    )
    forbidden = client.post(
        "/api/v1/agents/manager/run",
        headers=auth_header(viewer_login.json()["access_token"]),
        json={"task_input": "계획을 세워줘", "provider": "openai", "model": "gpt-test"},
    )
    assert forbidden.status_code == 403

    unknown = client.post(
        "/api/v1/agents/unknown/run",
        headers=headers,
        json={"task_input": "테스트", "provider": "openai", "model": "gpt-test"},
    )
    assert unknown.status_code == 400
