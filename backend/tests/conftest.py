import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-key-with-enough-length"
os.environ["ENVIRONMENT"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["REDIS_URL"] = ""
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "platform-admin@example.com"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "Platform1234"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.ai_models.base_provider import AIResponse, BaseProvider
from app.database.base import Base
from app.database.seed import bootstrap_platform_admin, seed_reference_data
from app.database.session import SessionLocal, engine
from app.main import app


class EchoProvider(BaseProvider):
    def __init__(self, name: str) -> None:
        self.name = name

    def generate(self, *, model: str, prompt: str, system_prompt: str | None = None) -> AIResponse:
        text = prompt if not system_prompt else f"{system_prompt}\n{prompt}"
        return AIResponse(
            text=text,
            prompt_tokens=1,
            completion_tokens=1,
            latency_ms=1,
            model_name=model,
            provider=self.name,
        )


@pytest.fixture
def fake_models():
    from tests.model_overrides import install_fake_models, remove_fake_models

    providers: dict[str, BaseProvider] = {
        "openai": EchoProvider("openai"),
        "anthropic": EchoProvider("anthropic"),
        "google": EchoProvider("google"),
    }
    install_fake_models(app, providers)
    yield
    remove_fake_models(app)

PLATFORM_EMAIL = "platform-admin@example.com"
PLATFORM_PASSWORD = "Platform1234"


def reset_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(delete(table))
        db.commit()
        seed_reference_data(db)
        bootstrap_platform_admin(db)
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        reset_database()
        yield test_client


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def register(client: TestClient, email: str, organization: str, password: str = "Password123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "organization_name": organization,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
