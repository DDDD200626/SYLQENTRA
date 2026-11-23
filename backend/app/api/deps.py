import uuid
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.database.session import get_db
from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.organization_service import OrganizationService
from app.services.tenant import TenantContext

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated")
    payload = decode_token(credentials.credentials, "access")
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise UnauthorizedError("Invalid token") from exc
    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Not authenticated")
    return user


def get_tenant_context(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_organization_id: Annotated[str | None, Header(alias="X-Organization-Id")] = None,
) -> TenantContext:
    return OrganizationService(db).resolve_tenant(user, x_organization_id)


def require_permissions(*codes: str):
    def checker(ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        missing = [code for code in codes if code not in ctx.permissions]
        if missing:
            raise ForbiddenError("Insufficient permissions")
        return ctx

    return checker
