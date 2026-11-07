import app.api.routes.admin as admin_route
from app.core.config import Settings
from app.db.models import Suggestion, User


def _settings_with_token(token: str | None) -> Settings:
    return Settings(_env_file=None, admin_token=token)


async def test_list_suggestions_returns_503_when_admin_is_disabled(client, monkeypatch) -> None:
    monkeypatch.setattr(admin_route, "get_settings", lambda: _settings_with_token(None))

    response = await client.get("/admin/suggestions")

    assert response.status_code == 503


async def test_list_suggestions_returns_403_without_the_admin_token(client, monkeypatch) -> None:
    monkeypatch.setattr(admin_route, "get_settings", lambda: _settings_with_token("s3cret"))

    response = await client.get("/admin/suggestions")

    assert response.status_code == 403


async def test_review_flips_suggestion_status_to_verified(client, monkeypatch, session) -> None:
    monkeypatch.setattr(admin_route, "get_settings", lambda: _settings_with_token("s3cret"))

    user = User(telegram_chat_id=9001, city="Recife", uf="PE")
    session.add(user)
    await session.flush()
    suggestion = Suggestion(user_id=user.id, city="Recife", uf="PE", text="corrigir endereço")
    session.add(suggestion)
    await session.commit()

    response = await client.post(
        f"/admin/suggestions/{suggestion.id}/review",
        json={"status": "verified"},
        headers={"X-Admin-Token": "s3cret"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "verified"
