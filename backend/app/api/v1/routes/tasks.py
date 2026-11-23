import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.schemas.common import TaskCreate, TaskListResponse, TaskRead
from app.services.task_service import TaskService
from app.services.tenant import TenantContext

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=TaskRead, status_code=201)
def create_task(
    payload: TaskCreate,
    request: Request,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = TaskService(db).create(ctx, payload, _client_ip(request))
    return TaskRead.model_validate(task)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_READ)),
    db: Session = Depends(get_db),
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TaskListResponse:
    items, total = TaskService(db).list_tasks(ctx.organization_id, status, limit, offset)
    return TaskListResponse(items=[TaskRead.model_validate(item) for item in items], total=total)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: uuid.UUID,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_READ)),
    db: Session = Depends(get_db),
) -> TaskRead:
    return TaskRead.model_validate(TaskService(db).get(ctx.organization_id, task_id))
