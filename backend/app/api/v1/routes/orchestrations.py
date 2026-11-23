from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager, get_model_manager
from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.orchestration.engine import Orchestrator
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
    state, task = Orchestrator(db, model_manager).run(
        ctx,
        request=payload.request,
        provider=payload.provider,
        model=payload.model,
        ip_address=request.client.host if request.client else None,
    )
    return OrchestrationResponse(
        task_id=str(task.id),
        status=state.status,
        plan=state.plan,
        outputs=state.outputs,
        final_output=state.final_output,
        error=state.error,
    )
