import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Task


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task

    def get_in_organization(self, organization_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        return self.db.scalar(
            select(Task).where(Task.id == task_id, Task.organization_id == organization_id)
        )

    def list_in_organization(
        self,
        organization_id: uuid.UUID,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        filters = [Task.organization_id == organization_id]
        if status is not None:
            filters.append(Task.status == status)
        total = int(self.db.scalar(select(func.count()).select_from(Task).where(*filters)) or 0)
        items = list(
            self.db.scalars(
                select(Task).where(*filters).order_by(Task.created_at.desc()).limit(limit).offset(offset)
            ).all()
        )
        return items, total
