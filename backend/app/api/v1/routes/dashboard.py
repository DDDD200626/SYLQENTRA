from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.schemas.common import DashboardResponse
from app.services.dashboard_service import DashboardService
from app.services.tenant import TenantContext

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.DASHBOARD_READ)),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    return DashboardService(db).build(ctx)
