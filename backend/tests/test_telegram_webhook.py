import app.api.routes.telegram as telegram_route
from app.core.config import Settings


def _settings_with_secret(secret: str | None) -> Settings:
    return Settings(_env_file=None, telegram_webhook_secret=secret)


async def test_webhook_rejects_request_with_wrong_secret(client, monkeypatch) -> None:
    monkeypatch.setattr(telegram_route, "get_settings", lambda: _settings_with_secret("s3cret"))

    response = await client.post(
        "/telegram/webhook",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )

    assert response.status_code == 403


async def test_webhook_rejects_request_with_no_secret_configured(client, monkeypatch) -> None:
    monkeypatch.setattr(telegram_route, "get_settings", lambda: _settings_with_secret(None))

    response = await client.post("/telegram/webhook", json={"update_id": 1})

    assert response.status_code == 403


async def test_webhook_accepts_matching_secret_and_always_returns_200(
    client, monkeypatch, fake_telegram_client
) -> None:
    monkeypatch.setattr(telegram_route, "get_settings", lambda: _settings_with_secret("s3cret"))
    monkeypatch.setattr(telegram_route, "get_telegram_client", lambda: fake_telegram_client)

    response = await client.post(
        "/telegram/webhook",
        json={"update_id": 1, "message": {"chat": {"id": 5001}, "text": "/start"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"},
    )

    assert response.status_code == 200
    assert fake_telegram_client.sent  # a saudação foi enviada
