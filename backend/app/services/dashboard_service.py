from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Agent, Approval, ModelUsage, Task
from app.schemas.common import DashboardResponse, DashboardTaskCounts
from app.services.tenant import TenantContext


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, ctx: TenantContext) -> DashboardResponse:
        organization_id = ctx.organization_id
        rows = self.db.execute(
            select(Task.status, func.count()).where(Task.organization_id == organization_id).group_by(Task.status)
        ).all()
        counts = {
            status: count
            for status, count in rows
            if status in DashboardTaskCounts.model_fields and status != "total"
        }
        tokens, cost = self.db.execute(
            select(
                func.coalesce(func.sum(ModelUsage.prompt_tokens + ModelUsage.completion_tokens), 0),
                func.coalesce(func.sum(ModelUsage.cost), 0),
            ).where(ModelUsage.organization_id == organization_id)
        ).one()
        agent_count = self.db.scalar(select(func.count()).select_from(Agent).where(Agent.organization_id == organization_id))
        pending_approvals = self.db.scalar(
            select(func.count())
            .select_from(Approval)
            .where(Approval.organization_id == organization_id, Approval.status == "pending")
        )
        task_counts = DashboardTaskCounts(total=sum(counts.values()), **counts)
        return DashboardResponse(
            organization_id=organization_id,
            agent_count=int(agent_count or 0),
            pending_approvals=int(pending_approvals or 0),
            total_tokens=int(tokens or 0),
            estimated_cost=Decimal(cost or 0),
            tasks=task_counts,
        )
