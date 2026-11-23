import pytest

from app.ai_models.base_provider import AIResponse, BaseProvider
from app.ai_models.model_manager import ModelManager


class FakeProvider(BaseProvider):
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[dict] = []

    def generate(self, *, model: str, prompt: str, system_prompt: str | None = None) -> AIResponse:
        self.calls.append({"model": model, "prompt": prompt, "system_prompt": system_prompt})
        return AIResponse(
            text=f"{self.name}:{prompt}",
            prompt_tokens=2,
            completion_tokens=3,
            latency_ms=4,
            model_name=model,
            provider=self.name,
        )


def test_model_manager_sends_the_request_to_the_selected_provider():
    openai = FakeProvider("openai")
    anthropic = FakeProvider("anthropic")
    google = FakeProvider("google")
    manager = ModelManager(providers={"openai": openai, "anthropic": anthropic, "google": google})

    response = manager.generate(
        provider="google",
        model="gemini-test",
        prompt="매출을 요약해줘",
        system_prompt="한 문장으로",
    )

    assert response.text == "google:매출을 요약해줘"
    assert response.provider == "google"
    assert google.calls == [
        {"model": "gemini-test", "prompt": "매출을 요약해줘", "system_prompt": "한 문장으로"}
    ]
    assert openai.calls == []
    assert anthropic.calls == []


def test_model_manager_rejects_an_unknown_provider():
    manager = ModelManager(providers={"openai": FakeProvider("openai")})
    with pytest.raises(ValueError, match="Unknown AI provider"):
        manager.generate(provider="missing", model="x", prompt="hello")