from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import ALL_PERMISSIONS, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS
from app.core.security import hash_password, validate_password
from app.models import AIProvider, Permission, Role, User

AI_PROVIDERS = (
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("google", "Google Gemini"),
)


def seed_reference_data(db: Session) -> None:
    permissions_by_code: dict[str, Permission] = {}
    for code, description in ALL_PERMISSIONS:
        permission = db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(code=code, description=description)
            db.add(permission)
            db.flush()
        permissions_by_code[code] = permission

    for name, description in ROLE_DESCRIPTIONS.items():
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, description=description)
            db.add(role)
            db.flush()
        role.permissions = [permissions_by_code[code] for code in ROLE_PERMISSIONS[name]]

    for name, display_name in AI_PROVIDERS:
        provider = db.scalar(select(AIProvider).where(AIProvider.name == name))
        if provider is None:
            db.add(AIProvider(name=name, display_name=display_name, is_active=True))

    db.commit()


def bootstrap_platform_admin(db: Session) -> None:
    email = settings.BOOTSTRAP_ADMIN_EMAIL
    password = settings.BOOTSTRAP_ADMIN_PASSWORD
    if not email or not password:
        return
    normalized = email.lower()
    existing = db.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        return
    validate_password(password)
    db.add(
        User(
            email=normalized,
            password_hash=hash_password(password),
            full_name="Platform Admin",
            is_active=True,
            is_platform_admin=True,
        )
    )
    db.commit()
