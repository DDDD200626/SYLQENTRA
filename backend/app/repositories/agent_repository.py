import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agent


class AgentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_in_organization(self, organization_id: uuid.UUID) -> list[Agent]:
        return list(self.db.scalars(select(Agent).where(Agent.organization_id == organization_id)).all())

    def add_all(self, agents: list[Agent]) -> None:
        self.db.add_all(agents)
        self.db.flush()
