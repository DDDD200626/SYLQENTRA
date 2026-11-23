from decimal import Decimal

from pydantic import BaseModel, Field


class AIGenerateRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=20000)
    system_prompt: str | None = Field(default=None, max_length=20000)


class AIGenerateResponse(BaseModel):
    text: str
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    estimated_cost: Decimal


class UsageSummaryResponse(BaseModel):
    monthly_token_limit: int
    tokens_used: int
    estimated_cost: Decimal


class UsageLimitUpdate(BaseModel):
    monthly_token_limit: int = Field(ge=0, le=100_000_000)


class AgentRunRequest(BaseModel):
    task_input: str = Field(min_length=1, max_length=20000)
    provider: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=100)
    tool: str | None = Field(default=None, max_length=100)


class OrchestrationRequest(BaseModel):
    request: str = Field(min_length=1, max_length=20000)
    provider: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=100)


class OrchestrationResponse(BaseModel):
    task_id: str
    status: str
    plan: list[str]
    outputs: dict[str, str]
    final_output: str
    error: str


class AgentRunResponse(BaseModel):
    agent_role: str
    status: str
    output: str
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
