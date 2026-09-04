from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration, sourced from environment variables (12-factor)."""

    app_name: str = "booking-service"
    # Default targets the local docker-compose postgres service; override via
    # the DATABASE_URL env var in any other environment.
    database_url: str = "postgresql+psycopg://booking:booking@localhost:5432/booking"


@lru_cache
def get_settings() -> Settings:
    return Settings()
