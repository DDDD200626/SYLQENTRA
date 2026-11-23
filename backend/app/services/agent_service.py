import uuid

from sqlalchemy.orm import Session

from app.models import Agent
from app.repositories.agent_repository import AgentRepository

ROLE_ORDER = ("manager", "research", "data", "developer", "document", "review", "automation")

DEFAULT_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "Manager",
        "manager",
        "업무를 분석하고 적절한 Agent에 분배한다.",
        "You are the SYLQENTRA Manager Agent. Analyze the user request, break it into tasks, and assign each task to a specialist agent. Do not invent completed work.",
    ),
    (
        "Research",
        "research",
        "자료 검색과 요약을 담당한다.",
        "You are the SYLQENTRA Research Agent. Gather and summarize relevant information. Cite the source of every claim you did not derive from the provided input.",
    ),
    (
        "Data",
        "data",
        "통계와 데이터 분석을 담당한다.",
        "You are the SYLQENTRA Data Agent. Analyze the supplied tabular data, show the calculations you used, and separate observations from recommendations.",
    ),
    (
        "Developer",
        "developer",
        "코드 분석과 생성 방향을 담당한다.",
        "You are the SYLQENTRA Developer Agent. Inspect code and issues, explain findings, and propose changes. Do not claim a change was applied unless a tool result says so.",
    ),
    (
        "Document",
        "document",
        "보고서와 문서를 작성한다.",
        "You are the SYLQENTRA Document Agent. Produce a structured document from the supplied analysis. Keep numbers identical to the source analysis.",
    ),
    (
        "Review",
        "review",
        "결과의 오류와 누락을 검증한다.",
        "You are the SYLQENTRA Review Agent. Check the draft for factual errors, missing inputs, and policy violations. Report findings before approving.",
    ),
    (
        "Automation",
        "automation",
        "승인된 외부 작업을 실행한다.",
        "You are the SYLQENTRA Automation Agent. Execute only tools that were explicitly allowed and approved. If approval is missing, stop and request it.",
    ),
)


class AgentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.agents = AgentRepository(db)

    def create_defaults(self, organization_id: uuid.UUID) -> None:
        rows = [
            Agent(
                organization_id=organization_id,
                name=name,
                role=role,
                description=description,
                system_prompt=prompt,
                is_active=True,
            )
            for name, role, description, prompt in DEFAULT_AGENTS
        ]
        self.agents.add_all(rows)

    def list_agents(self, organization_id: uuid.UUID) -> list[Agent]:
        order = {role: index for index, role in enumerate(ROLE_ORDER)}
        return sorted(self.agents.list_in_organization(organization_id), key=lambda agent: order.get(agent.role, 99))
