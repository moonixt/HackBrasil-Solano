from app.db.models import User
from app.domain.enums import OnboardingStep
from app.domain.location import LocationGuess
from app.domain.regions import Region
from app.onboarding.state_machine import (
    ONBOARDING_TRANSITIONS,
    ContactData,
    Incoming,
    KeyboardAction,
    reset_user,
)


def _user(step: OnboardingStep = OnboardingStep.AWAITING_CONTACT) -> User:
    return User(telegram_chat_id=123, onboarding_step=step)


def test_awaiting_contact_accepts_matching_contact_and_normalizes_phone() -> None:
    user = _user()
    contact = ContactData(phone_number="81999998888", first_name="Maria", last_name="Silva", user_id=123)

    reply = ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_CONTACT](user, Incoming(text=None, contact=contact))

    assert user.phone == "+5581999998888"
    assert user.name == "Maria Silva"
    assert user.onboarding_step == OnboardingStep.AWAITING_CITY
    assert reply.keyboard_action == KeyboardAction.REMOVE


def test_awaiting_contact_rejects_contact_from_another_user() -> None:
    user = _user()
    contact = ContactData(phone_number="81999998888", first_name="Maria", last_name=None, user_id=999)

    reply = ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_CONTACT](user, Incoming(text=None, contact=contact))

    assert user.onboarding_step == OnboardingStep.AWAITING_CONTACT
    assert reply.keyboard_action == KeyboardAction.SHOW_CONTACT


def test_awaiting_contact_rejects_invalid_phone_and_keeps_asking() -> None:
    user = _user()
    contact = ContactData(phone_number="123", first_name="Maria", last_name=None, user_id=123)

    reply = ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_CONTACT](user, Incoming(text=None, contact=contact))

    assert user.onboarding_step == OnboardingStep.AWAITING_CONTACT
    assert reply.keyboard_action == KeyboardAction.SHOW_CONTACT


def test_awaiting_city_sets_region_from_uf() -> None:
    user = _user(OnboardingStep.AWAITING_CITY)

    location = LocationGuess(city="Recife", uf="PE")
    ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_CITY](user, Incoming("Recife, PE", None, location))

    assert user.city == "Recife"
    assert user.uf == "PE"
    assert user.region == Region.NORDESTE
    assert user.onboarding_step == OnboardingStep.AWAITING_NEIGHBORHOOD


def test_awaiting_city_rejects_invalid_format() -> None:
    user = _user(OnboardingStep.AWAITING_CITY)

    ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_CITY](user, Incoming(text="não sei", contact=None))

    assert user.city is None
    assert user.onboarding_step == OnboardingStep.AWAITING_CITY


def test_awaiting_city_with_only_a_state_asks_for_the_city_and_keeps_the_uf() -> None:
    user = _user(OnboardingStep.AWAITING_CITY)
    step = ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_CITY]

    reply = step(user, Incoming("sp", None, LocationGuess(city=None, uf="SP")))
    assert "SP" in reply.text
    assert user.onboarding_step == OnboardingStep.AWAITING_CITY

    step(user, Incoming("Campinas", None, LocationGuess(city="Campinas", uf=None)))
    assert (user.city, user.uf, user.region) == ("Campinas", "SP", Region.SUDESTE)
    assert user.onboarding_step == OnboardingStep.AWAITING_NEIGHBORHOOD


def test_awaiting_city_with_neighborhood_skips_the_neighborhood_question() -> None:
    user = _user(OnboardingStep.AWAITING_CITY)

    reply = ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_CITY](
        user, Incoming("moro em recife, boa viagem", None, LocationGuess("Recife", "PE", "Boa Viagem"))
    )

    assert user.neighborhood == "Boa Viagem"
    assert user.onboarding_step == OnboardingStep.READY
    assert "agente do Nordeste" in reply.text


def test_awaiting_neighborhood_completes_onboarding_and_names_the_regional_agent() -> None:
    user = _user(OnboardingStep.AWAITING_NEIGHBORHOOD)
    user.region = Region.NORDESTE

    reply = ONBOARDING_TRANSITIONS[OnboardingStep.AWAITING_NEIGHBORHOOD](
        user, Incoming(text="Boa Viagem", contact=None)
    )

    assert user.neighborhood == "Boa Viagem"
    assert user.onboarding_step == OnboardingStep.READY
    assert "Nordeste" in reply.text


def test_reset_user_clears_onboarding_data() -> None:
    user = _user(OnboardingStep.READY)
    user.name = "Maria"
    user.phone = "+5581999998888"
    user.city = "Recife"
    user.uf = "PE"
    user.region = Region.NORDESTE
    user.neighborhood = "Boa Viagem"

    reset_user(user)

    assert user.onboarding_step == OnboardingStep.AWAITING_CONTACT
    assert user.name is None
    assert user.phone is None
    assert user.city is None
    assert user.uf is None
    assert user.region is None
    assert user.neighborhood is None
