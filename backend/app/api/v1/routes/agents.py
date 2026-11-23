from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager, get_model_manager
from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.schemas.ai import AgentRunRequest, AgentRunResponse
from app.schemas.common import AgentRead
from app.services.agent_execution_service import AgentExecutionService
from app.services.agent_service import AgentService
from app.services.tenant import TenantContext

router = APIRouter(prefix="/agents", tags=["agents"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[AgentRead])
def list_agents(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.AGENTS_READ)),
    db: Session = Depends(get_db),
) -> list[AgentRead]:
    return [AgentRead.model_validate(agent) for agent in AgentService(db).list_agents(ctx.organization_id)]


@router.post("/{role}/run", response_model=AgentRunResponse)
def run_agent(
    role: str,
    payload: AgentRunRequest,
    request: Request,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager),
) -> AgentRunResponse:
    result = AgentExecutionService(db, model_manager).run(
        ctx,
        role=role,
        task_input=payload.task_input,
        provider=payload.provider,
        model=payload.model,
        tool=payload.tool,
        ip_address=_client_ip(request),
    )
    return AgentRunResponse(
        agent_role=result.agent_role,
        status=result.status,
        output=result.output,
        provider=result.provider,
        model_name=result.model_name,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        latency_ms=result.latency_ms,
    )
