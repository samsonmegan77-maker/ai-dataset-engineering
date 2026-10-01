from .sqlite import SQLiteRepository


def create_repository(database_url=None):
    url = database_url or "sqlite:///./dataset_engineering.db"
    if not url.startswith("sqlite"):
        raise ValueError("PostgreSQL adapter is optional and not enabled in this build")
    return SQLiteRepository(url)
