from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, entry: AuditLog) -> None:
        self.db.add(entry)
        self.db.flush()
