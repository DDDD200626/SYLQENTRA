from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager
from app.models import Task
from app.orchestration.planner import parse_plan
from app.orchestration.state import OrchestrationState
from app.services.agent_execution_service import AgentExecutionService
from app.services.tenant import TenantContext


class Orchestrator:
    def __init__(self, db: Session, model_manager: ModelManager) -> None:
        self.db = db
        self.execution = AgentExecutionService(db, model_manager)

    def run(
        self,
        ctx: TenantContext,
        *,
        request: str,
        provider: str,
        model: str,
        ip_address: str | None,
    ) -> tuple[OrchestrationState, Task]:
        state = OrchestrationState(request=request)
        state.transition("planning")
        manager_result = self.execution.run(
            ctx,
            role="manager",
            task_input=(
                "Choose specialist roles from research, data, developer, document, automation. "
                "Reply with one role per line.\n"
                f"{request}"
            ),
            provider=provider,
            model=model,
            tool=None,
            ip_address=ip_address,
        )
        if manager_result.status != "completed":
            return self._fail(ctx, state, manager_result.output), self._save_task(ctx, state)
        state.plan = parse_plan(manager_result.output)
        state.transition("running")
        sections: list[str] = []
        for role in state.plan:
            result = self.execution.run(
                ctx,
                role=role,
                task_input=request,
                provider=provider,
                model=model,
                tool=None,
                ip_address=ip_address,
            )
            if result.status != "completed":
                return self._fail(ctx, state, result.output), self._save_task(ctx, state)
            state.outputs[role] = result.output
            sections.append(f"{role}:\n{result.output}")
        state.transition("reviewing")
        review = self.execution.run(
            ctx,
            role="review",
            task_input="\n\n".join(sections),
            provider=provider,
            model=model,
            tool=None,
            ip_address=ip_address,
        )
        if review.status != "completed":
            return self._fail(ctx, state, review.output), self._save_task(ctx, state)
        state.final_output = review.output
        state.transition("completed")
        return state, self._save_task(ctx, state)

    def _fail(self, ctx: TenantContext, state: OrchestrationState, message: str) -> OrchestrationState:
        state.error = message
        if state.status != "failed":
            state.transition("failed")
        return state

    def _save_task(self, ctx: TenantContext, state: OrchestrationState) -> Task:
        task = Task(
            organization_id=ctx.organization_id,
            created_by=ctx.user.id,
            title=state.request[:300],
            description=state.request,
            status=state.status,
            result={"plan": state.plan, "outputs": state.outputs, "final_output": state.final_output, "error": state.error},
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
