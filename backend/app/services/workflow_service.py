import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager
from app.core.exceptions import BadRequestError, NotFoundError
from app.database.base import utcnow
from app.models import Workflow, WorkflowEdge, WorkflowNode, WorkflowRun
from app.services.agent_execution_service import AgentExecutionService
from app.services.tenant import TenantContext


class WorkflowService:
    def __init__(self, db: Session, model_manager: ModelManager | None = None) -> None:
        self.db = db
        self.execution = AgentExecutionService(db, model_manager) if model_manager is not None else None

    def create(
        self,
        ctx: TenantContext,
        *,
        name: str,
        description: str,
        schedule_cron: str | None,
        nodes: list[dict],
        edges: list[dict],
    ) -> Workflow:
        workflow = Workflow(
            organization_id=ctx.organization_id,
            created_by=ctx.user.id,
            name=name,
            description=description,
            schedule_cron=schedule_cron,
            is_active=True,
        )
        self.db.add(workflow)
        self.db.flush()
        by_key: dict[str, WorkflowNode] = {}
        for node in nodes:
            row = WorkflowNode(
                organization_id=ctx.organization_id,
                workflow_id=workflow.id,
                node_key=node["node_key"],
                node_type=node["node_type"],
                config=node.get("config") or {},
                position=node.get("position"),
            )
            self.db.add(row)
            by_key[node["node_key"]] = row
        self.db.flush()
        for edge in edges:
            source = by_key.get(edge["source"])
            target = by_key.get(edge["target"])
            if source is None or target is None:
                raise BadRequestError("Workflow edge references an unknown node")
            self.db.add(
                WorkflowEdge(
                    organization_id=ctx.organization_id,
                    workflow_id=workflow.id,
                    source_node_id=source.id,
                    target_node_id=target.id,
                )
            )
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def list_workflows(self, organization_id: uuid.UUID) -> list[Workflow]:
        return list(
            self.db.scalars(select(Workflow).where(Workflow.organization_id == organization_id).order_by(Workflow.created_at)).all()
        )

    def execute(
        self,
        ctx: TenantContext,
        workflow_id: uuid.UUID,
        *,
        provider: str,
        model: str,
        task_input: str,
        ip_address: str | None,
    ) -> WorkflowRun:
        workflow = self._owned(ctx.organization_id, workflow_id)
        if self.execution is None:
            raise BadRequestError("Workflow execution is not configured")
        nodes = list(self.db.scalars(select(WorkflowNode).where(WorkflowNode.workflow_id == workflow.id)).all())
        edges = list(self.db.scalars(select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow.id)).all())
        run = WorkflowRun(
            organization_id=ctx.organization_id,
            workflow_id=workflow.id,
            triggered_by=ctx.user.id,
            status="running",
            started_at=utcnow(),
        )
        self.db.add(run)
        self.db.flush()
        outputs: list[str] = []
        for node in _ordered_nodes(nodes, edges):
            if node.node_type != "agent":
                continue
            role = str((node.config or {}).get("role", ""))
            result = self.execution.run(
                ctx,
                role=role,
                task_input=task_input,
                provider=provider,
                model=model,
                tool=None,
                ip_address=ip_address,
            )
            outputs.append(f"{role}: {result.output}")
            if result.status != "completed":
                run.status = result.status
                run.finished_at = utcnow()
                self.db.commit()
                return run
        run.status = "completed"
        run.finished_at = utcnow()
        self.db.commit()
        run.output_summary = "\n".join(outputs)  # type: ignore[attr-defined]
        return run

    def _owned(self, organization_id: uuid.UUID, workflow_id: uuid.UUID) -> Workflow:
        workflow = self.db.get(Workflow, workflow_id)
        if workflow is None or workflow.organization_id != organization_id:
            raise NotFoundError("Workflow not found")
        return workflow


def _ordered_nodes(nodes: list[WorkflowNode], edges: list[WorkflowEdge]) -> list[WorkflowNode]:
    by_id = {node.id: node for node in nodes}
    incoming = {node.id: 0 for node in nodes}
    outgoing: dict[uuid.UUID, list[uuid.UUID]] = {node.id: [] for node in nodes}
    for edge in edges:
        incoming[edge.target_node_id] = incoming.get(edge.target_node_id, 0) + 1
        outgoing.setdefault(edge.source_node_id, []).append(edge.target_node_id)
    ready = [node_id for node_id, count in incoming.items() if count == 0]
    ordered: list[WorkflowNode] = []
    while ready:
        current = ready.pop(0)
        ordered.append(by_id[current])
        for target in outgoing.get(current, []):
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    if len(ordered) != len(nodes):
        raise BadRequestError("Workflow graph contains a cycle")
    return ordered


def cron_is_due(expression: str | None, now: datetime) -> bool:
    if not expression or expression == "manual":
        return False
    parts = expression.split()
    if len(parts) != 5:
        return False
    values = [now.minute, now.hour, now.day, now.month, (now.weekday() + 1) % 7]
    for part, value in zip(parts, values, strict=True):
        if part != "*" and int(part) != value:
            return False
    return True
