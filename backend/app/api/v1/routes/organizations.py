import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_tenant_context, require_permissions
from app.core.exceptions import ForbiddenError
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models import User
from app.schemas.common import (
    MemberCreate,
    MemberRead,
    MemberUpdate,
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.services.organization_service import OrganizationService
from app.services.tenant import TenantContext

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[OrganizationRead])
def list_organizations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[OrganizationRead]:
    return [OrganizationRead.model_validate(item) for item in OrganizationService(db).list_organizations(user)]


@router.post("", response_model=OrganizationRead, status_code=201)
def create_organization(
    payload: OrganizationCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    if not user.is_platform_admin:
        raise ForbiddenError("Only a platform admin can create an organization")
    organization = OrganizationService(db).create_platform_organization(user, payload.name, _client_ip(request))
    return OrganizationRead.model_validate(organization)


@router.get("/current", response_model=OrganizationRead)
def current_organization(ctx: TenantContext = Depends(get_tenant_context)) -> OrganizationRead:
    return OrganizationRead.model_validate(ctx.organization)


@router.patch("/current", response_model=OrganizationRead)
def rename_organization(
    payload: OrganizationUpdate,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.ORGANIZATIONS_MANAGE)),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    organization = OrganizationService(db).rename(ctx, payload.name)
    return OrganizationRead.model_validate(organization)


@router.get("/members", response_model=list[MemberRead])
def list_members(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.USERS_READ)),
    db: Session = Depends(get_db),
) -> list[MemberRead]:
    return OrganizationService(db).list_members(ctx.organization_id)


@router.post("/members", response_model=MemberRead, status_code=201)
def add_member(
    payload: MemberCreate,
    request: Request,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.USERS_MANAGE)),
    db: Session = Depends(get_db),
) -> MemberRead:
    return OrganizationService(db).add_member(ctx, payload, _client_ip(request))


@router.patch("/members/{user_id}", response_model=MemberRead)
def update_member(
    user_id: uuid.UUID,
    payload: MemberUpdate,
    request: Request,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.USERS_MANAGE)),
    db: Session = Depends(get_db),
) -> MemberRead:
    return OrganizationService(db).update_member(ctx, user_id, payload, _client_ip(request))
