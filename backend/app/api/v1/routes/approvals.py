import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.permissions import PermissionCode
from app.database.base import utcnow
from app.database.session import get_db
from app.models import Approval
from app.services.tenant import TenantContext

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalDecision(BaseModel):
    decision: str


@router.get("")
def list_approvals(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.APPROVALS_READ)),
    db: Session = Depends(get_db),
) -> list[dict]:
    from sqlalchemy import select

    rows = db.scalars(select(Approval).where(Approval.organization_id == ctx.organization_id)).all()
    return [{"id": str(row.id), "status": row.status, "reason": row.reason} for row in rows]


@router.post("/{approval_id}/decide")
def decide(
    approval_id: uuid.UUID,
    payload: ApprovalDecision,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.APPROVALS_MANAGE)),
    db: Session = Depends(get_db),
) -> dict:
    if payload.decision not in {"approved", "rejected"}:
        raise BadRequestError("Decision must be approved or rejected")
    approval = db.get(Approval, approval_id)
    if approval is None or approval.organization_id != ctx.organization_id:
        raise NotFoundError("Approval not found")
    approval.status = payload.decision
    approval.decided_by = ctx.user.id
    approval.decided_at = utcnow()
    db.commit()
    return {"id": str(approval.id), "status": approval.status}
