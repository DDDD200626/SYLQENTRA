from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager, get_model_manager
from app.ai_models.usage_manager import UsageManager
from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.schemas.ai import AIGenerateRequest, AIGenerateResponse, UsageLimitUpdate, UsageSummaryResponse
from app.services.ai_service import AIService
from app.services.tenant import TenantContext

router = APIRouter(prefix="/ai", tags=["ai"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/generate", response_model=AIGenerateResponse)
def generate(
    payload: AIGenerateRequest,
    request: Request,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager),
) -> AIGenerateResponse:
    response, cost = AIService(db, model_manager).generate(
        ctx,
        provider=payload.provider,
        model=payload.model,
        prompt=payload.prompt,
        system_prompt=payload.system_prompt,
        ip_address=_client_ip(request),
    )
    return AIGenerateResponse(
        text=response.text,
        provider=response.provider,
        model_name=response.model_name,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        latency_ms=response.latency_ms,
        estimated_cost=cost,
    )


@router.get("/usage", response_model=UsageSummaryResponse)
def usage_summary(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.DASHBOARD_READ)),
    db: Session = Depends(get_db),
) -> UsageSummaryResponse:
    manager = UsageManager(db)
    return UsageSummaryResponse(
        monthly_token_limit=manager.monthly_token_limit(ctx.organization_id),
        tokens_used=manager.tokens_used_this_month(ctx.organization_id),
        estimated_cost=manager.cost_this_month(ctx.organization_id),
    )


@router.put("/usage-limit", response_model=UsageSummaryResponse)
def update_usage_limit(
    payload: UsageLimitUpdate,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.ORGANIZATIONS_MANAGE)),
    db: Session = Depends(get_db),
) -> UsageSummaryResponse:
    manager = UsageManager(db)
    manager.set_monthly_token_limit(ctx.organization_id, payload.monthly_token_limit)
    db.commit()
    return UsageSummaryResponse(
        monthly_token_limit=manager.monthly_token_limit(ctx.organization_id),
        tokens_used=manager.tokens_used_this_month(ctx.organization_id),
        estimated_cost=manager.cost_this_month(ctx.organization_id),
    )
