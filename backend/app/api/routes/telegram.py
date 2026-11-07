"""Webhook do Telegram: 403 com segredo errado, 200 sempre pro resto (a Bot API espera 200)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.telegram.client import get_telegram_client
from app.telegram.handlers import handle_update

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])

_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


@router.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    settings = get_settings()
    secret = request.headers.get(_SECRET_HEADER)
    if not settings.telegram_webhook_secret or secret != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403)

    payload = await request.json()
    client = get_telegram_client()
    try:
        await handle_update(payload, session, client)
    except Exception as exc:
        # Nunca logar o conteúdo da mensagem — só a classe do erro.
        logger.error("Falha ao processar update do Telegram: %s", type(exc).__name__)

    return Response(status_code=200)
