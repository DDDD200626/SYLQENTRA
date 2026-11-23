from types import SimpleNamespace

import pytest

from app.ai_models.openai_provider import OpenAIProvider


class FakeCompletions:
    def __init__(self) -> None:
        self.model = None
        self.messages = None

    def create(self, *, model, messages):
        self.model = model
        self.messages = messages
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="매출은 100입니다."))],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )


class FakeClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_openai_provider_maps_response_and_usage():
    client = FakeClient()
    provider = OpenAIProvider(client=client)

    response = provider.generate(
        model="gpt-test",
        prompt="이번 달 매출을 요약해줘",
        system_prompt="숫자만 유지해줘",
    )

    assert response.text == "매출은 100입니다."
    assert response.provider == "openai"
    assert response.model_name == "gpt-test"
    assert response.prompt_tokens == 11
    assert response.completion_tokens == 7
    assert response.latency_ms >= 0
    assert client.chat.completions.model == "gpt-test"
    assert client.chat.completions.messages[0] == {
        "role": "system",
        "content": "숫자만 유지해줘",
    }


def test_openai_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        OpenAIProvider()