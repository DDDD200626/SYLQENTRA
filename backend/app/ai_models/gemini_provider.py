import os
import time

from google import genai
from google.genai import types

from app.ai_models.base_provider import AIResponse, BaseProvider


class GeminiProvider(BaseProvider):
    name = "google"

    def __init__(self, api_key: str | None = None, client: genai.Client | None = None) -> None:
        if client is not None:
            self._client = client
            return
        key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is required")
        self._client = genai.Client(api_key=key)

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
    ) -> AIResponse:
        config = None
        if system_prompt:
            config = types.GenerateContentConfig(system_instruction=system_prompt)

        started = time.perf_counter()
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)

        usage = response.usage_metadata
        return AIResponse(
            text=response.text or "",
            prompt_tokens=usage.prompt_token_count or 0 if usage is not None else 0,
            completion_tokens=usage.candidates_token_count or 0 if usage is not None else 0,
            latency_ms=latency_ms,
            model_name=model,
            provider=self.name,
        )
