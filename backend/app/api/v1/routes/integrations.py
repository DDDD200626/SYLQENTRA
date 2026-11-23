from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.integrations.github.github_connector import GitHubConnector
from app.integrations.slack.slack_connector import SlackConnector
from app.services.audit_service import write_audit
from app.services.tenant import TenantContext

router = APIRouter(prefix="/integrations", tags=["integrations"])


class GitHubIssueQuery(BaseModel):
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)


class SlackMessage(BaseModel):
    channel: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=4000)


def _connector_factory():
    return GitHubConnector, SlackConnector


@router.post("/github/issues")
def github_issues(
    payload: GitHubIssueQuery,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_READ)),
    db: Session = Depends(get_db),
    x_integration_token: str = Header(alias="X-Integration-Token"),
) -> dict:
    connector = _connector_factory()[0](x_integration_token)
    try:
        issues = connector.list_issues(payload.owner, payload.repo)
    finally:
        connector.close()
    write_audit(
        db,
        action="integration.github.issues",
        resource_type="integration",
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        detail={"repo": f"{payload.owner}/{payload.repo}", "count": len(issues)},
    )
    db.commit()
    return {"issues": issues}


@router.post("/slack/messages", status_code=201)
def slack_message(
    payload: SlackMessage,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
    x_integration_token: str = Header(alias="X-Integration-Token"),
) -> dict:
    connector = _connector_factory()[1](x_integration_token)
    try:
        sent = connector.post_message(payload.channel, payload.text)
    finally:
        connector.close()
    write_audit(
        db,
        action="integration.slack.message",
        resource_type="integration",
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        detail={"channel": payload.channel},
    )
    db.commit()
    return sent
