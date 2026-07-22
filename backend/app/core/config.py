from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://lvr:lvr@localhost:5432/lvr"
    environment: str = "development"

    # The job consumer runs inside the API process (one machine, durable queue
    # in Postgres). Set false to run it as a separate Fly process group.
    worker_in_process: bool = True

    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_webhook_verify_token: str = ""

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Fly injects `postgres://…`; SQLAlchemy + asyncpg needs an explicit driver.

        Without this, the app boots and then fails to connect in production only.
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
