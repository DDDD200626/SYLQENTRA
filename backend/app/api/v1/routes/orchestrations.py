from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager, get_model_manager
from app.api.deps import require_permissions
from app.core.config import settings
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.orchestration.jobs import dispatch, enqueue
from app.schemas.ai import OrchestrationRequest, OrchestrationResponse
from app.services.tenant import TenantContext

router = APIRouter(prefix="/orchestrations", tags=["orchestrations"])


@router.post("", response_model=OrchestrationResponse, status_code=201)
def create_orchestration(
    payload: OrchestrationRequest,
    request: Request,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager),
) -> OrchestrationResponse:
    task = enqueue(
        db,
        ctx,
        request=payload.request,
        provider=payload.provider,
        model=payload.model,
        ip_address=request.client.host if request.client else None,
    )
    dispatch(task.id, model_manager, inline=settings.ENVIRONMENT == "test")
    db.refresh(task)
    result = task.result or {}
    return OrchestrationResponse(
        task_id=str(task.id),
        status=task.status,
        plan=list(result.get("plan") or []),
        outputs=dict(result.get("outputs") or {}),
        final_output=str(result.get("final_output") or ""),
        error=str(result.get("error") or ""),
    )
