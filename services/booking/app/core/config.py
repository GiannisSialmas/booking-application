from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration, sourced from environment variables (12-factor)."""

    app_name: str = "booking-service"


@lru_cache
def get_settings() -> Settings:
    return Settings()
