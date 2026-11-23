import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.repositories.audit_repository import AuditRepository


def write_audit(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    organization_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    detail: dict | None = None,
) -> None:
    AuditRepository(db).add(
        AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            detail=detail,
        )
    )
