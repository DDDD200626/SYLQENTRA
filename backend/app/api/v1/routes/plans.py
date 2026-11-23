from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.schemas.common import OrganizationRead
from app.services.organization_service import OrganizationService
from app.services.plans import PLANS
from app.services.tenant import TenantContext

router = APIRouter(tags=["plans"])


class PlanUpdate(BaseModel):
    plan: str


@router.get("/plans")
def list_plans() -> list[dict]:
    return [{"name": name, **details} for name, details in PLANS.items()]


@router.put("/organizations/current/plan", response_model=OrganizationRead)
def change_plan(
    payload: PlanUpdate,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.ORGANIZATIONS_MANAGE)),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    organization = OrganizationService(db).change_plan(ctx, payload.plan)
    return OrganizationRead.model_validate(organization)
