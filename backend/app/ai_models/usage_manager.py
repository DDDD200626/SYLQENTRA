import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.database.base import utcnow
from app.models import AIModel, AIProvider, ModelUsage, UsageLimit

DEFAULT_MONTHLY_TOKEN_LIMIT = 100_000
# USD per 1,000,000 tokens: (input, output). These are planning estimates, not an invoice.
PRICE_PER_MILLION = {
    "openai": (Decimal("2.50"), Decimal("10.00")),
    "anthropic": (Decimal("3.00"), Decimal("15.00")),
    "google": (Decimal("1.00"), Decimal("3.00")),
}
FALLBACK_PRICE = (Decimal("1.00"), Decimal("3.00"))


class UsageLimitExceeded(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, 429, "USAGE_LIMIT_EXCEEDED")


def estimate_cost(provider: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    input_price, output_price = PRICE_PER_MILLION.get(provider, FALLBACK_PRICE)
    cost = (Decimal(prompt_tokens) * input_price + Decimal(completion_tokens) * output_price) / Decimal(1_000_000)
    return cost.quantize(Decimal("0.000001"))


class UsageManager:
    def __init__(self, db: Session) -> None:
        self.db = db

    def monthly_token_limit(self, organization_id: uuid.UUID) -> int:
        row = self.db.scalar(select(UsageLimit).where(UsageLimit.organization_id == organization_id))
        if row is None:
            return DEFAULT_MONTHLY_TOKEN_LIMIT
        return row.monthly_token_limit

    def set_monthly_token_limit(self, organization_id: uuid.UUID, monthly_token_limit: int) -> UsageLimit:
        row = self.db.scalar(select(UsageLimit).where(UsageLimit.organization_id == organization_id))
        if row is None:
            row = UsageLimit(organization_id=organization_id, monthly_token_limit=monthly_token_limit)
            self.db.add(row)
        else:
            row.monthly_token_limit = monthly_token_limit
        self.db.flush()
        return row

    def tokens_used_this_month(self, organization_id: uuid.UUID) -> int:
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total = self.db.scalar(
            select(func.coalesce(func.sum(ModelUsage.prompt_tokens + ModelUsage.completion_tokens), 0)).where(
                ModelUsage.organization_id == organization_id,
                ModelUsage.created_at >= month_start,
            )
        )
        return int(total or 0)

    def cost_this_month(self, organization_id: uuid.UUID) -> Decimal:
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total = self.db.scalar(
            select(func.coalesce(func.sum(ModelUsage.cost), 0)).where(
                ModelUsage.organization_id == organization_id,
                ModelUsage.created_at >= month_start,
            )
        )
        return Decimal(total or 0)

    def assert_within_limit(self, organization_id: uuid.UUID) -> None:
        used = self.tokens_used_this_month(organization_id)
        limit = self.monthly_token_limit(organization_id)
        if used >= limit:
            raise UsageLimitExceeded(f"Monthly token limit reached ({used}/{limit})")

    def record(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID | None,
        provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
    ) -> ModelUsage:
        usage = ModelUsage(
            organization_id=organization_id,
            user_id=user_id,
            model_id=self._model_id(provider, model_name),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=estimate_cost(provider, prompt_tokens, completion_tokens),
            latency_ms=latency_ms,
            created_at=utcnow(),
        )
        self.db.add(usage)
        self.db.flush()
        return usage

    def _model_id(self, provider: str, model_name: str) -> uuid.UUID | None:
        provider_row = self.db.scalar(select(AIProvider).where(AIProvider.name == provider))
        if provider_row is None:
            return None
        model_row = self.db.scalar(
            select(AIModel).where(AIModel.provider_id == provider_row.id, AIModel.name == model_name)
        )
        if model_row is None:
            model_row = AIModel(provider_id=provider_row.id, name=model_name, is_active=True)
            self.db.add(model_row)
            self.db.flush()
        return model_row.id
