from decimal import Decimal

from sqlalchemy.orm import Session

from app.ai_models.base_provider import AIResponse
from app.ai_models.model_manager import ModelManager
from app.ai_models.usage_manager import UsageManager, estimate_cost
from app.core.exceptions import BadRequestError
from app.services.audit_service import write_audit
from app.services.tenant import TenantContext


class AIService:
    def __init__(self, db: Session, model_manager: ModelManager) -> None:
        self.db = db
        self.model_manager = model_manager
        self.usage = UsageManager(db)

    def generate(
        self,
        ctx: TenantContext,
        *,
        provider: str,
        model: str,
        prompt: str,
        system_prompt: str | None,
        ip_address: str | None,
    ) -> tuple[AIResponse, Decimal]:
        self.usage.assert_within_limit(ctx.organization_id)
        try:
            response = self.model_manager.generate(
                provider=provider,
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
            )
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc
        usage = self.usage.record(
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            provider=response.provider,
            model_name=response.model_name,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=response.latency_ms,
        )
        write_audit(
            self.db,
            action="ai.generate",
            resource_type="model_usage",
            resource_id=str(usage.id),
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            ip_address=ip_address,
            detail={"provider": response.provider, "model": response.model_name},
        )
        self.db.commit()
        return response, estimate_cost(response.provider, response.prompt_tokens, response.completion_tokens)
