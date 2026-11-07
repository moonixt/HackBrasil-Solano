from sqlalchemy import select

from app.db.models import User
from app.domain.enums import OnboardingStep
from app.domain.regions import Region
from app.telegram.handlers import handle_update
from tests.telegram_factories import contact_update, text_update


async def _load_user(session, chat_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_chat_id == chat_id))
    return result.scalar_one()


async def test_full_onboarding_flow_reaches_ready_with_region_nordeste(session, fake_telegram_client) -> None:
    chat_id = 1001

    await handle_update(text_update(chat_id, "/start"), session, fake_telegram_client)
    await handle_update(contact_update(chat_id, "81999998888", "Maria"), session, fake_telegram_client)
    await handle_update(text_update(chat_id, "Recife, PE"), session, fake_telegram_client)
    await handle_update(text_update(chat_id, "Boa Viagem"), session, fake_telegram_client)

    user = await _load_user(session, chat_id)
    assert user.onboarding_step == OnboardingStep.READY
    assert user.region == Region.NORDESTE
    assert user.neighborhood == "Boa Viagem"
    assert user.phone == "+5581999998888"
    assert "Nordeste" in fake_telegram_client.sent[-1].text


async def test_invalid_phone_is_rejected_and_contact_is_asked_again(session, fake_telegram_client) -> None:
    chat_id = 1002

    await handle_update(text_update(chat_id, "/start"), session, fake_telegram_client)
    await handle_update(contact_update(chat_id, "123", "Maria"), session, fake_telegram_client)

    user = await _load_user(session, chat_id)
    assert user.onboarding_step == OnboardingStep.AWAITING_CONTACT
    assert "telefone" in fake_telegram_client.sent[-1].text.lower()


async def test_invalid_city_format_is_rejected_and_asked_again(session, fake_telegram_client) -> None:
    chat_id = 1003

    await handle_update(text_update(chat_id, "/start"), session, fake_telegram_client)
    await handle_update(contact_update(chat_id, "81999998888", "Maria"), session, fake_telegram_client)
    await handle_update(text_update(chat_id, "não sei"), session, fake_telegram_client)

    user = await _load_user(session, chat_id)
    assert user.onboarding_step == OnboardingStep.AWAITING_CITY


async def test_local_command_restarts_city_step_without_losing_phone(session, fake_telegram_client) -> None:
    chat_id = 1004
    await handle_update(text_update(chat_id, "/start"), session, fake_telegram_client)
    await handle_update(contact_update(chat_id, "81999998888", "Maria"), session, fake_telegram_client)
    await handle_update(text_update(chat_id, "Recife, PE"), session, fake_telegram_client)
    await handle_update(text_update(chat_id, "Boa Viagem"), session, fake_telegram_client)

    await handle_update(text_update(chat_id, "/local"), session, fake_telegram_client)

    user = await _load_user(session, chat_id)
    assert user.onboarding_step == OnboardingStep.AWAITING_CITY
    assert user.phone == "+5581999998888"  # /local não refaz o cadastro de telefone
