import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utcnow
from app.models import RefreshToken, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def save_refresh_token(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        row = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=utcnow(),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    def revoke_all_refresh_tokens(self, user_id: uuid.UUID, revoked_at: datetime) -> None:
        rows = self.db.scalars(
            select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        ).all()
        for row in rows:
            row.revoked_at = revoked_at
