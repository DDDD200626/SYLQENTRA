from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base.base_agent import AgentResult
from app.agents.registry import create_agent
from app.ai_models.model_manager import ModelManager
from app.ai_models.usage_manager import UsageManager
from app.core.exceptions import BadRequestError
from app.database.base import utcnow
from app.models import Agent, AgentRun
from app.services.audit_service import write_audit
from app.services.tenant import TenantContext


class AgentExecutionService:
    def __init__(self, db: Session, model_manager: ModelManager) -> None:
        self.db = db
        self.model_manager = model_manager
        self.usage = UsageManager(db)

    def run(
        self,
        ctx: TenantContext,
        *,
        role: str,
        task_input: str,
        provider: str,
        model: str,
        tool: str | None,
        ip_address: str | None,
    ) -> AgentResult:
        try:
            agent = create_agent(role, self.model_manager, provider, model)
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc

        started = datetime.now(timezone.utc)
        if tool is None or tool in agent.allowed_tools:
            self.usage.assert_within_limit(ctx.organization_id)
        try:
            result = agent.run(task_input, tool)
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc

        if result.status == "completed":
            self.usage.record(
                organization_id=ctx.organization_id,
                user_id=ctx.user.id,
                provider=result.provider,
                model_name=result.model_name,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                latency_ms=result.latency_ms,
            )
        self._save_run(ctx, result, task_input, tool, started)
        write_audit(
            self.db,
            action="agent.run",
            resource_type="agent",
            resource_id=result.agent_role,
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            ip_address=ip_address,
            detail={"status": result.status, "provider": provider, "model": model, "tool": tool},
        )
        self.db.commit()
        return result

    def _save_run(
        self,
        ctx: TenantContext,
        result: AgentResult,
        task_input: str,
        tool: str | None,
        started: datetime,
    ) -> None:
        agent_row = self.db.scalar(
            select(Agent).where(Agent.organization_id == ctx.organization_id, Agent.role == result.agent_role)
        )
        self.db.add(
            AgentRun(
                organization_id=ctx.organization_id,
                agent_id=agent_row.id if agent_row is not None else None,
                status=result.status,
                input_data={"task_input": task_input, "tool": tool},
                output_data={"output": result.output},
                error_message=None if result.status == "completed" else result.output,
                started_at=started,
                finished_at=utcnow(),
            )
        )
