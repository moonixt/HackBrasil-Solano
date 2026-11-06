from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


def _existing_env_files() -> tuple[Path, ...]:
    return tuple(
        path for path in (REPO_ROOT / ".env", BACKEND_ROOT / ".env") if path.is_file()
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_existing_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Solano"
    database_url: str = "postgresql+asyncpg://solano:solano@localhost:5432/solano"

    @field_validator("database_url")
    @classmethod
    def use_asyncpg_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgres://")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
