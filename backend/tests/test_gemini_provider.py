from types import SimpleNamespace

import pytest

from app.ai_models.gemini_provider import GeminiProvider


class FakeModels:
    def __init__(self) -> None:
        self.kwargs = None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            text="요약이 완료되었습니다.",
            usage_metadata=SimpleNamespace(prompt_token_count=8, candidates_token_count=4),
        )


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModels()


def test_gemini_provider_maps_response_and_usage():
    client = FakeClient()
    provider = GeminiProvider(client=client)

    response = provider.generate(
        model="gemini-test",
        prompt="이번 달 매출을 요약해줘",
        system_prompt="한 문장으로 답해줘",
    )

    assert response.text == "요약이 완료되었습니다."
    assert response.provider == "google"
    assert response.model_name == "gemini-test"
    assert response.prompt_tokens == 8
    assert response.completion_tokens == 4
    assert response.latency_ms >= 0
    assert client.models.kwargs["model"] == "gemini-test"
    assert client.models.kwargs["contents"] == "이번 달 매출을 요약해줘"
    assert client.models.kwargs["config"].system_instruction == "한 문장으로 답해줘"


def test_gemini_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GeminiProvider()
