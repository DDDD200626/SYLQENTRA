import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager, get_model_manager
from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.services.tenant import TenantContext
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowNodeInput(BaseModel):
    node_key: str
    node_type: str
    config: dict = Field(default_factory=dict)
    position: dict | None = None


class WorkflowEdgeInput(BaseModel):
    source: str
    target: str


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    schedule_cron: str | None = None
    nodes: list[WorkflowNodeInput]
    edges: list[WorkflowEdgeInput]


class WorkflowExecute(BaseModel):
    provider: str
    model: str
    task_input: str


@router.get("")
def list_workflows(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_READ)),
    db: Session = Depends(get_db),
) -> list[dict]:
    workflows = WorkflowService(db).list_workflows(ctx.organization_id)
    return [
        {"id": str(item.id), "name": item.name, "schedule_cron": item.schedule_cron, "is_active": item.is_active}
        for item in workflows
    ]


@router.post("", status_code=201)
def create_workflow(
    payload: WorkflowCreate,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
) -> dict:
    workflow = WorkflowService(db).create(
        ctx,
        name=payload.name,
        description=payload.description,
        schedule_cron=payload.schedule_cron,
        nodes=[item.model_dump() for item in payload.nodes],
        edges=[item.model_dump() for item in payload.edges],
    )
    return {"id": str(workflow.id), "name": workflow.name}


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: uuid.UUID,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_READ)),
    db: Session = Depends(get_db),
) -> dict:
    return WorkflowService(db).detail(ctx.organization_id, workflow_id)


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowExecute,
    request: Request,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager),
) -> dict:
    run = WorkflowService(db, model_manager).execute(
        ctx,
        workflow_id,
        provider=payload.provider,
        model=payload.model,
        task_input=payload.task_input,
        ip_address=request.client.host if request.client else None,
    )
    return {"id": str(run.id), "status": run.status}
