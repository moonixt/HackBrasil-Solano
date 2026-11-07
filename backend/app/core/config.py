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

    # Bot do Telegram (api.telegram.org/bot<token>) e o segredo que valida o webhook.
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None

    # LLM do agente, por qualquer API compatível com a da OpenAI (chat completions + tools).
    # Sem chave, o bot responde pelo formatador determinístico de fallback.
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"
    # Busca na web embutida do provedor (browser_search da Groq). Desligue para outros provedores.
    llm_web_search: bool = True

    # Token do painel de revisão de sugestões (/admin/*). Sem valor, a API fica desligada (503).
    admin_token: str | None = None

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
