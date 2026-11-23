from collections.abc import Callable

from app.ai_models.base_provider import AIResponse, BaseProvider
from app.ai_models.claude_provider import ClaudeProvider
from app.ai_models.gemini_provider import GeminiProvider
from app.ai_models.openai_provider import OpenAIProvider

ProviderFactory = Callable[[], BaseProvider]

FACTORIES: dict[str, ProviderFactory] = {
    "openai": OpenAIProvider,
    "anthropic": ClaudeProvider,
    "google": GeminiProvider,
}


class ModelManager:
    def __init__(self, providers: dict[str, BaseProvider] | None = None) -> None:
        self._providers = providers

    def generate(
        self,
        *,
        provider: str,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
    ) -> AIResponse:
        selected = self._resolve(provider)
        return selected.generate(model=model, prompt=prompt, system_prompt=system_prompt)

    def _resolve(self, provider: str) -> BaseProvider:
        if self._providers is not None:
            selected = self._providers.get(provider)
            if selected is None:
                raise ValueError(self._unknown_provider_message(provider))
            return selected
        factory = FACTORIES.get(provider)
        if factory is None:
            raise ValueError(self._unknown_provider_message(provider))
        return factory()

    def _unknown_provider_message(self, provider: str) -> str:
        known = ", ".join(sorted(self._providers if self._providers is not None else FACTORIES))
        return f"Unknown AI provider '{provider}'. Known providers: {known}"


def get_model_manager() -> ModelManager:
    return ModelManager()
