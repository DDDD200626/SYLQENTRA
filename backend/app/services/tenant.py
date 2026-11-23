import uuid
from dataclasses import dataclass

from app.models import Organization, User


@dataclass
class TenantContext:
    user: User
    organization: Organization
    role_name: str
    permissions: set[str]

    @property
    def organization_id(self) -> uuid.UUID:
        return self.organization.id
