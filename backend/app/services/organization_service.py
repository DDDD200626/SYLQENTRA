import re
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import ASSIGNABLE_ROLES
from app.models import Membership, Organization, User
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import MemberCreate, MemberRead, MemberUpdate, OrganizationMembershipRead
from app.ai_models.usage_manager import UsageManager
from app.services.agent_service import AgentService
from app.services.plans import PLANS
from app.services.audit_service import write_audit
from app.services.tenant import TenantContext
from app.core.security import hash_password, validate_password


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60] or "org"


class OrganizationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.organizations = OrganizationRepository(db)
        self.users = UserRepository(db)

    def create_organization(self, name: str, owner: User | None, owner_role: str = "organization_admin") -> Organization:
        cleaned = name.strip()
        if not cleaned:
            raise BadRequestError("Organization name is required")
        slug = self._unique_slug(cleaned)
        organization = self.organizations.add(Organization(name=cleaned, slug=slug, plan="free", is_active=True))
        AgentService(self.db).create_defaults(organization.id)
        UsageManager(self.db).set_monthly_token_limit(organization.id, PLANS["free"]["monthly_token_limit"])
        if owner is not None:
            self._attach_member(organization, owner, owner_role)
        return organization

    def list_organizations(self, user: User) -> list[Organization]:
        if user.is_platform_admin:
            return self.organizations.list_all()
        return [item.organization for item in self.organizations.list_memberships_for_user(user.id)]

    def list_visible(self, user: User) -> list[OrganizationMembershipRead]:
        if user.is_platform_admin:
            memberships = {
                item.organization_id: item.role.name
                for item in self.organizations.list_memberships_for_user(user.id)
            }
            return [
                OrganizationMembershipRead(
                    id=organization.id,
                    name=organization.name,
                    slug=organization.slug,
                    role=memberships.get(organization.id, "super_admin"),
                )
                for organization in self.organizations.list_all()
            ]
        return [self._membership_read(item) for item in self.organizations.list_memberships_for_user(user.id)]

    def resolve_tenant(self, user: User, organization_header: str | None) -> TenantContext:
        memberships = self.organizations.list_memberships_for_user(user.id)
        organization_id = self._parse_org_header(organization_header) if organization_header else None

        if organization_id is not None:
            organization = self.organizations.get(organization_id)
            if organization is None or not organization.is_active:
                raise NotFoundError("Organization not found")
            membership = next((item for item in memberships if item.organization_id == organization_id), None)
            if membership is not None:
                return self._context_from_membership(user, membership)
            if user.is_platform_admin:
                return self._platform_context(user, organization)
            raise ForbiddenError("You are not a member of this organization")

        if len(memberships) == 1:
            return self._context_from_membership(user, memberships[0])
        if len(memberships) == 0 and user.is_platform_admin:
            raise BadRequestError("X-Organization-Id header is required")
        if len(memberships) > 1:
            raise BadRequestError("X-Organization-Id header is required")
        raise ForbiddenError("No organization membership")

    def add_member(
        self,
        ctx: TenantContext,
        payload: MemberCreate,
        ip_address: str | None,
    ) -> MemberRead:
        if payload.role not in ASSIGNABLE_ROLES:
            raise BadRequestError("Role cannot be assigned")
        email = payload.email.strip().lower()
        user = self.users.get_by_email(email)
        if user is None:
            if not payload.password:
                raise BadRequestError("Password is required for a new user")
            validate_password(payload.password)
            user = self.users.add(
                User(
                    email=email,
                    password_hash=hash_password(payload.password),
                    full_name=payload.full_name.strip(),
                    is_active=True,
                    is_platform_admin=False,
                )
            )
        elif self.organizations.get_membership(ctx.organization_id, user.id) is not None:
            raise ConflictError("User is already a member of this organization")

        membership = self._attach_member(ctx.organization, user, payload.role)
        write_audit(
            self.db,
            action="organization.member_added",
            resource_type="membership",
            resource_id=str(membership.id),
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            ip_address=ip_address,
            detail={"email": user.email, "role": payload.role},
        )
        self.db.commit()
        return self._member_read(membership)

    def update_member(
        self,
        ctx: TenantContext,
        user_id: uuid.UUID,
        payload: MemberUpdate,
        ip_address: str | None,
    ) -> MemberRead:
        if payload.role is None and payload.is_active is None:
            raise BadRequestError("No changes requested")
        if payload.role is not None and payload.role not in ASSIGNABLE_ROLES:
            raise BadRequestError("Role cannot be assigned")
        membership = self.organizations.get_membership(ctx.organization_id, user_id)
        if membership is None:
            raise NotFoundError("Member not found")
        if user_id == ctx.user.id and payload.is_active is False:
            raise BadRequestError("You cannot deactivate your own membership")

        removing_admin = membership.role.name == "organization_admin" and (
            payload.is_active is False or (payload.role is not None and payload.role != "organization_admin")
        )
        if removing_admin and self.organizations.count_active_role(ctx.organization_id, "organization_admin") <= 1:
            raise BadRequestError("The organization must keep one active organization admin")

        if payload.role is not None:
            role = self.organizations.get_role_by_name(payload.role)
            if role is None:
                raise BadRequestError("Role cannot be assigned")
            membership.role = role
        if payload.is_active is not None:
            membership.is_active = payload.is_active
        write_audit(
            self.db,
            action="organization.member_updated",
            resource_type="membership",
            resource_id=str(membership.id),
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            ip_address=ip_address,
            detail={"target_user_id": str(user_id), "role": payload.role, "is_active": payload.is_active},
        )
        self.db.commit()
        self.db.refresh(membership)
        return self._member_read(membership)

    def list_members(self, organization_id: uuid.UUID) -> list[MemberRead]:
        return [self._member_read(item) for item in self.organizations.list_members(organization_id)]

    def create_platform_organization(self, actor: User, name: str, ip_address: str | None) -> Organization:
        organization = self.create_organization(name, owner=None)
        write_audit(
            self.db,
            action="organization.created",
            resource_type="organization",
            resource_id=str(organization.id),
            organization_id=organization.id,
            user_id=actor.id,
            ip_address=ip_address,
        )
        self.db.commit()
        return organization

    def change_plan(self, ctx: TenantContext, plan_name: str) -> Organization:
        if plan_name not in PLANS:
            raise BadRequestError("Unknown subscription plan")
        ctx.organization.plan = plan_name
        UsageManager(self.db).set_monthly_token_limit(ctx.organization_id, PLANS[plan_name]["monthly_token_limit"])
        self.db.commit()
        return ctx.organization

    def rename(self, ctx: TenantContext, name: str) -> Organization:
        cleaned = name.strip()
        if not cleaned:
            raise BadRequestError("Organization name is required")
        ctx.organization.name = cleaned
        self.db.commit()
        return ctx.organization

    def _unique_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while self.organizations.get_by_slug(slug) is not None:
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _attach_member(self, organization: Organization, user: User, role_name: str) -> Membership:
        role = self.organizations.get_role_by_name(role_name)
        if role is None:
            raise BadRequestError("Role is not configured")
        return self.organizations.add_membership(
            Membership(organization_id=organization.id, user_id=user.id, role_id=role.id, is_active=True)
        )

    def _context_from_membership(self, user: User, membership: Membership) -> TenantContext:
        permissions = {permission.code for permission in membership.role.permissions}
        if user.is_platform_admin:
            permissions = self._all_permission_codes()
        return TenantContext(
            user=user,
            organization=membership.organization,
            role_name="super_admin" if user.is_platform_admin else membership.role.name,
            permissions=permissions,
        )

    def _platform_context(self, user: User, organization: Organization) -> TenantContext:
        return TenantContext(
            user=user,
            organization=organization,
            role_name="super_admin",
            permissions=self._all_permission_codes(),
        )

    def _all_permission_codes(self) -> set[str]:
        from app.models import Permission
        from sqlalchemy import select

        return set(self.db.scalars(select(Permission.code)).all())

    def _membership_read(self, membership: Membership) -> OrganizationMembershipRead:
        return OrganizationMembershipRead(
            id=membership.organization.id,
            name=membership.organization.name,
            slug=membership.organization.slug,
            role=membership.role.name,
        )

    def _member_read(self, membership: Membership) -> MemberRead:
        return MemberRead(
            user_id=membership.user.id,
            email=membership.user.email,
            full_name=membership.user.full_name,
            role=membership.role.name,
            is_active=membership.is_active,
        )

    @staticmethod
    def _parse_org_header(value: str) -> uuid.UUID:
        try:
            return uuid.UUID(value)
        except ValueError as exc:
            raise BadRequestError("X-Organization-Id must be a UUID") from exc
