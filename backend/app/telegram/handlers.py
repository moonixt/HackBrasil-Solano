"""Ponto de entrada de cada Update do Telegram: parse na borda, comandos fixos, o resto vai ao agente."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import messages
from app.agent import memory
from app.agent.agent import respond
from app.db.models import Suggestion, User
from app.domain.phone import normalize_br_phone
from app.telegram.client import TelegramClientProtocol
from app.telegram.keyboards import CONTACT_KEYBOARD, REMOVE_KEYBOARD
from app.telegram.schemas import TelegramContact, TelegramUpdate


async def _get_or_create_user(session: AsyncSession, chat_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_chat_id == chat_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_chat_id=chat_id)
        session.add(user)
        await session.flush()
    return user


def _save_contact(user: User, contact: TelegramContact) -> str:
    if contact.user_id != user.telegram_chat_id:
        return messages.MSG_INVALID_PHONE
    phone = normalize_br_phone(contact.phone_number)
    if phone is None:
        return messages.MSG_INVALID_PHONE
    user.phone = phone
    user.name = f"{contact.first_name} {contact.last_name}" if contact.last_name else contact.first_name
    return messages.MSG_PHONE_SAVED


def _command_reply(session: AsyncSession, user: User, text: str) -> tuple[str, dict | None] | None:
    """Comandos fixos. None quando a mensagem não é comando e deve ir ao agente."""
    if text == "/start":
        memory.forget(user.telegram_chat_id)
        return messages.MSG_GREETING, CONTACT_KEYBOARD
    if text == "/ajuda":
        return messages.MSG_HELP, None
    if text == "/local":
        memory.forget(user.telegram_chat_id)
        user.city = user.uf = user.region = user.neighborhood = None
        return messages.MSG_LOCAL_RESET, None
    if text.startswith("/sugerir"):
        suggestion = text.removeprefix("/sugerir").strip()
        if not suggestion:
            return messages.MSG_SUGGEST_EMPTY, None
        if user.city is None or user.uf is None:
            return messages.MSG_SUGGEST_NEEDS_LOCATION, None
        session.add(Suggestion(user_id=user.id, city=user.city, uf=user.uf, text=suggestion))
        return messages.MSG_SUGGEST_THANKS, None
    return None


async def handle_update(update: dict, session: AsyncSession, client: TelegramClientProtocol) -> None:
    parsed = TelegramUpdate.model_validate(update)
    if parsed.message is None:
        return

    message = parsed.message
    chat_id = message.chat.id
    text = (message.text or "").strip()
    user = await _get_or_create_user(session, chat_id)

    if message.contact is not None:
        reply, markup = _save_contact(user, message.contact), REMOVE_KEYBOARD
    elif not text:
        reply, markup = messages.MSG_HELP, None
    elif (command := _command_reply(session, user, text)) is not None:
        reply, markup = command
    else:
        await client.send_chat_action(chat_id, "typing")
        reply, markup = await respond(session, user, text), None

    await session.commit()
    await client.send_message(chat_id, reply, reply_markup=markup)
