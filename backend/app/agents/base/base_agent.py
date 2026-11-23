from dataclasses import dataclass

from app.ai_models.model_manager import ModelManager


@dataclass(frozen=True)
class AgentResult:
    agent_role: str
    status: str
    output: str
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int


class BaseAgent:
    role: str
    description: str
    system_prompt: str
    allowed_tools: tuple[str, ...] = ()

    def __init__(self, model_manager: ModelManager, provider: str, model: str) -> None:
        self.model_manager = model_manager
        self.provider = provider
        self.model = model

    def run(self, task_input: str, tool: str | None = None) -> AgentResult:
        if tool and tool not in self.allowed_tools:
            return AgentResult(
                agent_role=self.role,
                status="blocked",
                output=f"Tool '{tool}' is not allowed for the {self.role} agent.",
                provider=self.provider,
                model_name=self.model,
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=0,
            )
        response = self.model_manager.generate(
            provider=self.provider,
            model=self.model,
            prompt=self.build_user_prompt(task_input, tool),
            system_prompt=self.system_prompt,
        )
        return AgentResult(
            agent_role=self.role,
            status="completed",
            output=response.text,
            provider=response.provider,
            model_name=response.model_name,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=response.latency_ms,
        )

    def build_user_prompt(self, task_input: str, tool: str | None) -> str:
        allowed = ", ".join(self.allowed_tools) if self.allowed_tools else "none"
        tool_line = f"Requested tool: {tool}\n" if tool else ""
        return f"Role: {self.role}\nAllowed tools: {allowed}\n{tool_line}Task:\n{task_input}"
