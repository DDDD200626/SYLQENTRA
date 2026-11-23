from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class AIResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    model_name: str
    provider: str

class BaseProvider(ABC):
    name: str

    @abstractmethod
    def generate(
            self,
            *,
            model: str,
            prompt: str,
            system_prompt: str | None = None,
    ) -> AIResponse:
        """선택한 모델에 질문 하나를 보내고 공통 형식의 응답을 받는다."""

