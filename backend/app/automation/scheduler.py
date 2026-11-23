from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager
from app.models import Workflow
from app.services.workflow_service import WorkflowService, cron_is_due


def run_due_workflows(db: Session, model_manager: ModelManager, now: datetime) -> list[str]:
    """Run active workflows whose cron matches. A Celery beat process can call this."""
    workflows = list(db.scalars(select(Workflow).where(Workflow.is_active.is_(True))).all())
    service = WorkflowService(db, model_manager)
    started: list[str] = []
    for workflow in workflows:
        if not cron_is_due(workflow.schedule_cron, now):
            continue
        if workflow.created_by is None:
            continue
        from app.services.organization_service import OrganizationService

        user_memberships = OrganizationService(db).organizations.list_memberships_for_user(workflow.created_by)
        membership = next((item for item in user_memberships if item.organization_id == workflow.organization_id), None)
        if membership is None:
            continue
        ctx = OrganizationService(db)._context_from_membership(membership.user, membership)
        service.execute(
            ctx,
            workflow.id,
            provider="openai",
            model=workflow.name,
            task_input=workflow.description or workflow.name,
            ip_address=None,
        )
        started.append(str(workflow.id))
    return started
