import os
import time

from openai import OpenAI

from app.ai_models.base_provider import AIResponse, BaseProvider


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None, client: OpenAI | None = None) -> None:
        if client is not None:
            self._client = client
            return
        key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY is required")
        self._client = OpenAI(api_key=key)

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
    ) -> AIResponse:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        started = time.perf_counter()
        response = self._client.chat.completions.create(model=model, messages=messages)
        latency_ms = int((time.perf_counter() - started) * 1000)

        usage = response.usage
        text = response.choices[0].message.content or ""
        return AIResponse(
            text=text,
            prompt_tokens=usage.prompt_tokens if usage is not None else 0,
            completion_tokens=usage.completion_tokens if usage is not None else 0,
            latency_ms=latency_ms,
            model_name=model,
            provider=self.name,
        )
