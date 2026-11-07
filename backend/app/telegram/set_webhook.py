"""Configura o webhook do bot para apontar para a API pública.

Uso: uv run python -m app.telegram.set_webhook https://seu-dominio.exemplo
"""

import asyncio
import sys

from app.core.config import get_settings
from app.telegram.client import TelegramClient


async def run(public_url: str) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_webhook_secret:
        raise RuntimeError("TELEGRAM_BOT_TOKEN e TELEGRAM_WEBHOOK_SECRET precisam estar configurados")

    client = TelegramClient(settings.telegram_bot_token)
    try:
        webhook_url = f"{public_url.rstrip('/')}/telegram/webhook"
        result = await client.set_webhook(webhook_url, settings.telegram_webhook_secret)
        print(result)
    finally:
        await client.aclose()


def main() -> None:
    if len(sys.argv) != 2:
        print("uso: uv run python -m app.telegram.set_webhook <url_publica>")
        raise SystemExit(1)
    asyncio.run(run(sys.argv[1]))


if __name__ == "__main__":
    main()
