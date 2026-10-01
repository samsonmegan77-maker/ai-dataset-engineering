from __future__ import annotations
from functools import lru_cache
from dataset_engineering.persistence.factory import create_repository
from dataset_engineering.application.services import ApplicationService

@lru_cache(maxsize=4)
def get_service(database_url: str | None = None) -> ApplicationService:
    return ApplicationService(create_repository(database_url))
