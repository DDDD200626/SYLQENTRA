import pytest

from app.ai_models.base_provider import AIResponse, BaseProvider


class FakeProvider(BaseProvider):
    name = "fake"

    def generate(
            self,
            *,
            model: str,
            prompt: str,
            system_prompt: str | None = None,
    ) -> AIResponse:
        return AIResponse(
            text=f"echo:{prompt}",
            prompt_tokens=1,
            completion_tokens=2,
            latency_ms=3,
            model_name=model,
            provider=self.name,
        )


def test_fake_provider_returns_usage_fields():
    response = FakeProvider().generate(model="fake-model", prompt="hello")
    assert response.text == "echo:hello"
    assert response.provider == "fake"
    assert response.model_name == "fake-model"
    assert response.prompt_tokens == 1
    assert response.completion_tokens == 2
    assert response.latency_ms == 3


def test_base_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseProvider()