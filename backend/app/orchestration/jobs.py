import threading
import uuid

from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager
from app.database.session import SessionLocal
from app.models import Organization, Task, User
from app.orchestration.engine import Orchestrator
from app.services.tenant import TenantContext

MAX_ATTEMPTS = 3


def enqueue(
    db: Session,
    ctx: TenantContext,
    *,
    request: str,
    provider: str,
    model: str,
    ip_address: str | None,
) -> Task:
    task = Task(
        organization_id=ctx.organization_id,
        created_by=ctx.user.id,
        title=request[:300],
        description=request,
        status="pending",
        result={
            "request": request,
            "provider": provider,
            "model": model,
            "ip_address": ip_address,
            "role_name": ctx.role_name,
            "attempts": 0,
            "plan": [],
            "outputs": {},
            "final_output": "",
            "error": "",
        },
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def process(task_id: uuid.UUID, model_manager: ModelManager) -> None:
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None or task.created_by is None:
            return
        user = db.get(User, task.created_by)
        organization = db.get(Organization, task.organization_id)
        if user is None or organization is None:
            return
        payload = dict(task.result or {})
        ctx = TenantContext(
            user=user,
            organization=organization,
            role_name=str(payload.get("role_name") or "organization_admin"),
            permissions=set(),
        )
        last_error = ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            task = db.get(Task, task_id)
            if task is None:
                return
            payload = dict(task.result or {})
            payload["attempts"] = attempt
            task.status = "running"
            task.result = payload
            db.commit()
            try:
                state, task = Orchestrator(db, model_manager).run(
                    ctx,
                    request=str(payload.get("request") or task.description),
                    provider=str(payload.get("provider") or ""),
                    model=str(payload.get("model") or ""),
                    ip_address=payload.get("ip_address"),
                    task=task,
                )
            except Exception as exc:
                db.rollback()
                task = db.get(Task, task_id)
                last_error = str(exc)
                if task is not None and attempt == MAX_ATTEMPTS:
                    task.status = "failed"
                    task.result = {**(task.result or {}), "attempts": attempt, "error": last_error}
                    db.commit()
                continue
            if state.status == "completed":
                return
            last_error = state.error
            if attempt == MAX_ATTEMPTS and task.status != "failed":
                task.status = "failed"
                task.result = {**(task.result or {}), "attempts": attempt, "error": last_error}
                db.commit()
    finally:
        db.close()


def dispatch(task_id: uuid.UUID, model_manager: ModelManager, *, inline: bool) -> None:
    if inline:
        process(task_id, model_manager)
        return
    threading.Thread(target=process, args=(task_id, model_manager), daemon=True).start()
