from types import SimpleNamespace

import pytest

from app.ai_models.claude_provider import ClaudeProvider


class FakeMessages:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(text="검토 결과 이상 없습니다.")],
            usage=SimpleNamespace(input_tokens=9, output_tokens=6),
        )


class FakeClient:
    def __init__(self) -> None:
        self.messages = FakeMessages()


def test_claude_provider_maps_response_and_usage():
    client = FakeClient()
    provider = ClaudeProvider(client=client)

    response = provider.generate(
        model="claude-test",
        prompt="매출 분석을 검토해줘",
        system_prompt="오류만 지적해줘",
    )

    assert response.text == "검토 결과 이상 없습니다."
    assert response.provider == "anthropic"
    assert response.model_name == "claude-test"
    assert response.prompt_tokens == 9
    assert response.completion_tokens == 6
    assert response.latency_ms >= 0
    assert client.messages.kwargs["model"] == "claude-test"
    assert client.messages.kwargs["system"] == "오류만 지적해줘"
    assert client.messages.kwargs["messages"] == [
        {"role": "user", "content": "매출 분석을 검토해줘"}
    ]


def test_claude_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ClaudeProvider()