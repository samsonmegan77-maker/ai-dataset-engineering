from __future__ import annotations
from functools import lru_cache
from dataset_engineering.config import Settings
from dataset_engineering.persistence.factory import create_repository
from dataset_engineering.application.services import ApplicationService

@lru_cache(maxsize=4)
def get_service() -> ApplicationService:
    settings = Settings.from_env()
    return ApplicationService(create_repository(settings.database_url))
