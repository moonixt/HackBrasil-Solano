from app.core.config import Settings


def test_settings_rewrites_postgres_url_to_asyncpg(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://solano:secret@db.internal:5432/solano",
    )

    settings = Settings(_env_file=None)

    assert settings.database_url == (
        "postgresql+asyncpg://solano:secret@db.internal:5432/solano"
    )


def test_settings_defaults_leave_optional_integrations_disabled() -> None:
    settings = Settings(_env_file=None)

    assert settings.telegram_bot_token is None
    assert settings.telegram_webhook_secret is None
    assert settings.llm_api_key is None
    assert settings.llm_base_url == "https://api.groq.com/openai/v1"
    assert settings.admin_token is None
