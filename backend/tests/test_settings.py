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
