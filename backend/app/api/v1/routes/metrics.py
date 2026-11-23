from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models import AgentRun, Task
from app.services.tenant import TenantContext

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_class=PlainTextResponse)
def metrics(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.DASHBOARD_READ)),
    db: Session = Depends(get_db),
) -> str:
    task_rows = db.execute(
        select(Task.status, func.count()).where(Task.organization_id == ctx.organization_id).group_by(Task.status)
    ).all()
    run_rows = db.execute(
        select(AgentRun.status, func.count()).where(AgentRun.organization_id == ctx.organization_id).group_by(AgentRun.status)
    ).all()
    lines = ["# TYPE sylqentra_tasks gauge", "# TYPE sylqentra_agent_runs gauge"]
    for status, count in task_rows:
        lines.append(f'sylqentra_tasks{{status="{status}"}} {count}')
    for status, count in run_rows:
        lines.append(f'sylqentra_agent_runs{{status="{status}"}} {count}')
    if len(lines) == 2:
        lines.append('sylqentra_tasks{status="pending"} 0')
    return "\n".join(lines) + "\n"
