"""Ponto de entrada de cada Update do Telegram: parse na borda, resto é domínio puro."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.service import answer as agent_answer
from app.db.models import Suggestion, User
from app.domain.enums import OnboardingStep
from app.onboarding import messages
from app.onboarding.state_machine import (
    ONBOARDING_TRANSITIONS,
    ContactData,
    Incoming,
    KeyboardAction,
    reset_user,
)
from app.telegram.client import TelegramClientProtocol
from app.telegram.keyboards import markup_for
from app.telegram.schemas import TelegramUpdate


async def _get_or_create_user(session: AsyncSession, chat_id: int) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.telegram_chat_id == chat_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user, False

    user = User(telegram_chat_id=chat_id, onboarding_step=OnboardingStep.AWAITING_CONTACT)
    session.add(user)
    await session.flush()
    return user, True


async def _send(client: TelegramClientProtocol, chat_id: int, text: str, action: KeyboardAction) -> None:
    await client.send_message(chat_id, text, reply_markup=markup_for(action))


async def handle_update(update: dict, session: AsyncSession, client: TelegramClientProtocol) -> None:
    parsed = TelegramUpdate.model_validate(update)
    if parsed.message is None:
        return

    message = parsed.message
    chat_id = message.chat.id
    text = (message.text or "").strip()

    user, created = await _get_or_create_user(session, chat_id)

    if created or text == "/start":
        if not created:
            reset_user(user)
        await session.commit()
        await _send(client, chat_id, messages.MSG_GREETING, KeyboardAction.SHOW_CONTACT)
        return

    if text == "/ajuda":
        await _send(client, chat_id, messages.MSG_HELP, KeyboardAction.NONE)
        return

    if text == "/local":
        user.onboarding_step = OnboardingStep.AWAITING_CITY
        await session.commit()
        await _send(client, chat_id, messages.MSG_ASK_CITY, KeyboardAction.NONE)
        return

    if text.startswith("/sugerir"):
        suggestion_text = text.removeprefix("/sugerir").strip()
        if not suggestion_text:
            await _send(client, chat_id, messages.MSG_SUGGEST_EMPTY, KeyboardAction.NONE)
            return
        if user.city is None or user.uf is None:
            await _send(client, chat_id, messages.MSG_SUGGEST_NEEDS_LOCATION, KeyboardAction.NONE)
            return
        session.add(Suggestion(user_id=user.id, city=user.city, uf=user.uf, text=suggestion_text))
        await session.commit()
        await _send(client, chat_id, messages.MSG_SUGGEST_THANKS, KeyboardAction.NONE)
        return

    if user.onboarding_step == OnboardingStep.READY:
        if not text:
            await _send(client, chat_id, messages.MSG_HELP, KeyboardAction.NONE)
            return
        reply_text = await agent_answer(session, user, text)
        await _send(client, chat_id, reply_text, KeyboardAction.NONE)
        return

    contact = None
    if message.contact is not None:
        contact = ContactData(
            phone_number=message.contact.phone_number,
            first_name=message.contact.first_name,
            last_name=message.contact.last_name,
            user_id=message.contact.user_id,
        )
    incoming = Incoming(text=text or None, contact=contact)
    handler = ONBOARDING_TRANSITIONS[user.onboarding_step]
    reply = handler(user, incoming)
    await session.commit()
    await _send(client, chat_id, reply.text, reply.keyboard_action)
