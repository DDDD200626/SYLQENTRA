from typing import Any

from app.ai_models.base_provider import BaseProvider
from app.ai_models.model_manager import ModelManager, get_model_manager


def install_fake_models(application: Any, providers: dict[str, BaseProvider]) -> None:
    application.dependency_overrides[get_model_manager] = lambda: ModelManager(providers=providers)


def remove_fake_models(application: Any) -> None:
    application.dependency_overrides.pop(get_model_manager, None)
