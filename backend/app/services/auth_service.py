from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    validate_password,
    verify_password,
)
from app.database.base import utcnow
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest, UserUpdateRequest
from app.schemas.common import OrganizationMembershipRead, TokenResponse, UserRead
from app.services.audit_service import write_audit
from app.services.organization_service import OrganizationService


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.organizations = OrganizationService(db)

    def register(self, payload: RegisterRequest, ip_address: str | None) -> TokenResponse:
        validate_password(payload.password)
        email = payload.email.lower()
        if self.users.get_by_email(email) is not None:
            raise ConflictError("Email already registered")
        user = self.users.add(
            User(
                email=email,
                password_hash=hash_password(payload.password),
                full_name=payload.full_name.strip(),
                is_active=True,
                is_platform_admin=False,
            )
        )
        organization = self.organizations.create_organization(payload.organization_name, user)
        write_audit(
            self.db,
            action="auth.register",
            resource_type="user",
            resource_id=str(user.id),
            organization_id=organization.id,
            user_id=user.id,
            ip_address=ip_address,
        )
        response = self._issue_tokens(user)
        self.db.commit()
        return response

    def login(self, payload: LoginRequest, ip_address: str | None) -> TokenResponse:
        user = self.users.get_by_email(payload.email.lower())
        if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        write_audit(
            self.db,
            action="auth.login",
            resource_type="user",
            resource_id=str(user.id),
            user_id=user.id,
            ip_address=ip_address,
        )
        response = self._issue_tokens(user)
        self.db.commit()
        return response

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, "refresh")
        stored = self.users.get_refresh_token(hash_token(refresh_token))
        if stored is None:
            raise UnauthorizedError("Invalid token")
        if stored.revoked_at is not None:
            self.users.revoke_all_refresh_tokens(stored.user_id, utcnow())
            self.db.commit()
            raise UnauthorizedError("Refresh token reuse detected")
        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError("Invalid token")
        user = self.users.get(stored.user_id)
        if user is None or not user.is_active or str(user.id) != payload["sub"]:
            raise UnauthorizedError("Invalid token")
        stored.revoked_at = utcnow()
        response = self._issue_tokens(user)
        self.db.commit()
        return response

    def logout(self, refresh_token: str, ip_address: str | None) -> None:
        stored = self.users.get_refresh_token(hash_token(refresh_token))
        if stored is None:
            raise UnauthorizedError("Invalid token")
        if stored.revoked_at is None:
            stored.revoked_at = utcnow()
        write_audit(
            self.db,
            action="auth.logout",
            resource_type="user",
            resource_id=str(stored.user_id),
            user_id=stored.user_id,
            ip_address=ip_address,
        )
        self.db.commit()

    def change_password(self, user: User, payload: ChangePasswordRequest, ip_address: str | None) -> None:
        if not verify_password(payload.current_password, user.password_hash):
            raise BadRequestError("Current password is incorrect")
        validate_password(payload.new_password)
        user.password_hash = hash_password(payload.new_password)
        self.users.revoke_all_refresh_tokens(user.id, utcnow())
        write_audit(
            self.db,
            action="auth.change_password",
            resource_type="user",
            resource_id=str(user.id),
            user_id=user.id,
            ip_address=ip_address,
        )
        self.db.commit()

    def update_profile(self, user: User, payload: UserUpdateRequest) -> User:
        user.full_name = payload.full_name.strip()
        self.db.commit()
        return user

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.users.save_refresh_token(user.id, hash_token(refresh_token), expires_at)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead.model_validate(user),
            organizations=self.organizations.list_visible(user),
        )
