"""Environment-aware runtime configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./dataset_engineering.db"
    cors_origins: tuple[str, ...] = ()
    max_upload_bytes: int = 10 * 1024 * 1024
    max_records: int = 100_000
    max_page_size: int = 100
    log_level: str = "INFO"
    environment: str = "development"

    @classmethod
    def from_env(cls) -> "Settings":
        origins = tuple(
            x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()
        )
        return cls(
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            cors_origins=origins,
            max_upload_bytes=max(
                1, int(os.getenv("MAX_UPLOAD_BYTES", str(cls.max_upload_bytes)))
            ),
            max_records=max(1, int(os.getenv("MAX_RECORDS", str(cls.max_records)))),
            max_page_size=max(
                1, min(1000, int(os.getenv("MAX_PAGE_SIZE", str(cls.max_page_size))))
            ),
            log_level=os.getenv("LOG_LEVEL", cls.log_level).upper(),
            environment=os.getenv("ENVIRONMENT", cls.environment),
        )
