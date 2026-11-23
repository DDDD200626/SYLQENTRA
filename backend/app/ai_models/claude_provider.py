import os
import time

from anthropic import Anthropic

from app.ai_models.base_provider import AIResponse, BaseProvider


class ClaudeProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, client: Anthropic | None = None) -> None:
        if client is not None:
            self._client = client
            return
        key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        self._client = Anthropic(api_key=key)

    def generate(
            self,
            *,
            model: str,
            prompt: str,
            system_prompt: str | None = None,
    ) -> AIResponse:
        kwargs: dict = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        started = time.perf_counter()
        response = self._client.messages.create(**kwargs)
        latency_ms = int((time.perf_counter() - started) * 1000)

        blocks = response.content or []
        text = blocks[0].text if blocks else ""
        usage = response.usage
        return AIResponse(
            text=text,
            prompt_tokens=usage.input_tokens if usage is not None else 0,
            completion_tokens=usage.output_tokens if usage is not None else 0,
            latency_ms=latency_ms,
            model_name=model,
            provider=self.name,
        )