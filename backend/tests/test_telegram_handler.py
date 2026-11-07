from sqlalchemy import select

from app.db.models import User
from app.telegram.handlers import handle_update
from app.telegram.keyboards import CONTACT_KEYBOARD, REMOVE_KEYBOARD
from tests.telegram_factories import contact_update, text_update


async def _user(session, chat_id: int) -> User:
    return (await session.execute(select(User).where(User.telegram_chat_id == chat_id))).scalar_one()


async def test_start_greets_and_offers_the_optional_contact_button(session, fake_telegram_client) -> None:
    await handle_update(text_update(5001, "/start"), session, fake_telegram_client)

    sent = fake_telegram_client.sent[-1]
    assert "Solano" in sent.text
    assert sent.reply_markup == CONTACT_KEYBOARD


async def test_first_message_is_answered_without_any_signup(session, fake_telegram_client) -> None:
    await handle_update(text_update(5002, "onde me vacino?"), session, fake_telegram_client)

    assert len(fake_telegram_client.sent) == 1
    assert "cidade e o estado" in fake_telegram_client.sent[-1].text


async def test_shared_contact_saves_a_br_phone(session, fake_telegram_client) -> None:
    await handle_update(contact_update(5003, "+55 81 99999-8888", "Ana", "Lima"), session, fake_telegram_client)

    user = await _user(session, 5003)
    assert (user.phone, user.name) == ("+5581999998888", "Ana Lima")
    assert fake_telegram_client.sent[-1].reply_markup == REMOVE_KEYBOARD


async def test_contact_of_someone_else_is_not_saved(session, fake_telegram_client) -> None:
    await handle_update(contact_update(5004, "5581999998888", "Outro", user_id=42), session, fake_telegram_client)

    assert (await _user(session, 5004)).phone is None


async def test_local_command_clears_the_location(session, fake_telegram_client) -> None:
    await handle_update(text_update(5005, "Recife, PE, Boa Viagem"), session, fake_telegram_client)
    await handle_update(text_update(5005, "/local"), session, fake_telegram_client)

    user = await _user(session, 5005)
    assert (user.city, user.uf, user.neighborhood) == (None, None, None)


async def test_non_text_message_gets_the_help(session, fake_telegram_client) -> None:
    sticker = {"update_id": 9, "message": {"chat": {"id": 5006}}}

    await handle_update(sticker, session, fake_telegram_client)

    assert "/local" in fake_telegram_client.sent[-1].text
