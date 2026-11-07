"""Cliente fino para a Bot API do Telegram, sobre httpx. Sem python-telegram-bot."""

from typing import Any, Protocol

import httpx

from app.core.config import get_settings


class TelegramClientProtocol(Protocol):
    """O subconjunto da Bot API que o Solano usa — a fake de teste implementa isto."""

    async def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> Any: ...


class TelegramClient:
    def __init__(self, token: str, http_client: httpx.AsyncClient | None = None) -> None:
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._client = http_client or httpx.AsyncClient(timeout=30.0)

    async def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> Any:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        response = await self._client.post(f"{self._base_url}/sendMessage", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_updates(self, offset: int | None = None, timeout: int = 30) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        response = await self._client.get(
            f"{self._base_url}/getUpdates", params=params, timeout=timeout + 10
        )
        response.raise_for_status()
        return response.json()["result"]

    async def set_webhook(self, url: str, secret: str) -> Any:
        response = await self._client.post(
            f"{self._base_url}/setWebhook", json={"url": url, "secret_token": secret}
        )
        response.raise_for_status()
        return response.json()

    async def delete_webhook(self) -> Any:
        response = await self._client.post(f"{self._base_url}/deleteWebhook")
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()


_singleton: TelegramClient | None = None


def get_telegram_client() -> TelegramClient:
    """Singleton do processo. A rota de webhook chama esta função por nome — nos testes,
    monkeypatch.setattr no módulo da rota substitui por uma fake sem precisar de token."""
    global _singleton
    if _singleton is None:
        token = get_settings().telegram_bot_token
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")
        _singleton = TelegramClient(token)
    return _singleton
