import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.common import TaskCreate
from app.services.audit_service import write_audit
from app.services.tenant import TenantContext

TASK_STATUSES = {
    "pending",
    "planning",
    "running",
    "reviewing",
    "completed",
    "failed",
    "cancelled",
    "awaiting_approval",
}


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tasks = TaskRepository(db)

    def create(self, ctx: TenantContext, payload: TaskCreate, ip_address: str | None) -> Task:
        task = self.tasks.add(
            Task(
                organization_id=ctx.organization_id,
                created_by=ctx.user.id,
                title=payload.title.strip(),
                description=payload.description.strip(),
                status="pending",
            )
        )
        write_audit(
            self.db,
            action="task.created",
            resource_type="task",
            resource_id=str(task.id),
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            ip_address=ip_address,
            detail={"title": task.title},
        )
        self.db.commit()
        return task

    def get(self, organization_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        task = self.tasks.get_in_organization(organization_id, task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task

    def list_tasks(
        self,
        organization_id: uuid.UUID,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        if status is not None and status not in TASK_STATUSES:
            raise BadRequestError("Unknown task status")
        return self.tasks.list_in_organization(organization_id, status, limit, offset)
