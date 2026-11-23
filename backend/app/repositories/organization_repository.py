import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Membership, Organization, Role


class OrganizationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, organization_id: uuid.UUID) -> Organization | None:
        return self.db.get(Organization, organization_id)

    def get_by_slug(self, slug: str) -> Organization | None:
        return self.db.scalar(select(Organization).where(Organization.slug == slug))

    def add(self, organization: Organization) -> Organization:
        self.db.add(organization)
        self.db.flush()
        return organization

    def list_all(self) -> list[Organization]:
        return list(self.db.scalars(select(Organization).order_by(Organization.created_at)).all())

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))

    def add_membership(self, membership: Membership) -> Membership:
        self.db.add(membership)
        self.db.flush()
        return membership

    def get_membership(self, organization_id: uuid.UUID, user_id: uuid.UUID) -> Membership | None:
        return self.db.scalar(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.user_id == user_id,
            )
        )

    def list_memberships_for_user(self, user_id: uuid.UUID) -> list[Membership]:
        return list(
            self.db.scalars(
                select(Membership).where(Membership.user_id == user_id, Membership.is_active.is_(True))
            ).all()
        )

    def list_members(self, organization_id: uuid.UUID) -> list[Membership]:
        return list(
            self.db.scalars(select(Membership).where(Membership.organization_id == organization_id)).all()
        )

    def count_active_role(self, organization_id: uuid.UUID, role_name: str) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Membership)
                .join(Role, Membership.role_id == Role.id)
                .where(
                    Membership.organization_id == organization_id,
                    Membership.is_active.is_(True),
                    Role.name == role_name,
                )
            )
            or 0
        )
