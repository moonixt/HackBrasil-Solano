"""Long polling local, para desenvolvimento sem expor um webhook público.

Uso: uv run python -m app.telegram.polling
"""

import asyncio
import logging

from app.core.config import get_settings
from app.db.session import async_session_factory
from app.telegram.client import TelegramClient
from app.telegram.handlers import handle_update

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")

    client = TelegramClient(settings.telegram_bot_token)
    await client.delete_webhook()  # polling e webhook não coexistem na Bot API
    offset: int | None = None
    logger.info("Polling do Solano iniciado")
    try:
        while True:
            updates = await client.get_updates(offset=offset, timeout=30)
            for update in updates:
                offset = update["update_id"] + 1
                async with async_session_factory() as session:
                    try:
                        await handle_update(update, session, client)
                    except Exception as exc:
                        logger.error(
                            "Falha ao processar update %s: %s",
                            update.get("update_id"),
                            type(exc).__name__,
                        )
    finally:
        await client.aclose()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())


if __name__ == "__main__":
    main()
