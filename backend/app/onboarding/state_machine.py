"""Máquina de estados do onboarding: um handler puro por passo, despachado por tabela.

Cada handler só lê/escreve atributos simples do User (nenhuma query, nenhum I/O) —
quem persiste é o chamador (app.telegram.handlers), depois de aplicar o retorno.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from app.agent.personas import REGIONAL_AGENTS
from app.db.models import User
from app.domain.enums import OnboardingStep
from app.domain.location import LocationGuess
from app.domain.phone import normalize_br_phone
from app.domain.regions import UF_TO_REGION
from app.onboarding import messages


class KeyboardAction(Enum):
    NONE = "none"
    SHOW_CONTACT = "show_contact"
    REMOVE = "remove"


@dataclass(frozen=True)
class ContactData:
    phone_number: str
    first_name: str
    last_name: str | None
    user_id: int | None


@dataclass(frozen=True)
class Incoming:
    text: str | None
    contact: ContactData | None
    location: LocationGuess | None = None


@dataclass(frozen=True)
class OnboardingReply:
    text: str
    keyboard_action: KeyboardAction = KeyboardAction.NONE


def _handle_awaiting_contact(user: User, incoming: Incoming) -> OnboardingReply:
    contact = incoming.contact
    if contact is None or contact.user_id != user.telegram_chat_id:
        return OnboardingReply(messages.MSG_ASK_CONTACT_AGAIN, KeyboardAction.SHOW_CONTACT)

    phone = normalize_br_phone(contact.phone_number)
    if phone is None:
        return OnboardingReply(messages.MSG_INVALID_PHONE, KeyboardAction.SHOW_CONTACT)

    user.phone = phone
    user.name = f"{contact.first_name} {contact.last_name}" if contact.last_name else contact.first_name
    user.onboarding_step = OnboardingStep.AWAITING_CITY
    return OnboardingReply(messages.MSG_ASK_CITY, KeyboardAction.REMOVE)


def _finish(user: User) -> OnboardingReply:
    user.onboarding_step = OnboardingStep.READY
    agent_name = REGIONAL_AGENTS[user.region].name
    return OnboardingReply(messages.MSG_READY.format(agent_name=agent_name))


def _handle_awaiting_city(user: User, incoming: Incoming) -> OnboardingReply:
    guess = incoming.location
    if guess is None:
        return OnboardingReply(messages.MSG_INVALID_CITY)

    if guess.city is None:
        if guess.uf is None:
            return OnboardingReply(messages.MSG_INVALID_CITY)
        # Só o estado ("sp"): guarda a UF para a próxima mensagem trazer só a cidade.
        user.uf = guess.uf
        return OnboardingReply(messages.MSG_ONLY_UF.format(uf=guess.uf))

    uf = guess.uf or user.uf
    if uf is None:
        return OnboardingReply(messages.MSG_INVALID_CITY)

    user.city = guess.city
    user.uf = uf
    user.region = UF_TO_REGION[uf]
    if guess.neighborhood:
        user.neighborhood = guess.neighborhood
        return _finish(user)
    user.onboarding_step = OnboardingStep.AWAITING_NEIGHBORHOOD
    return OnboardingReply(messages.MSG_ASK_NEIGHBORHOOD)


def _handle_awaiting_neighborhood(user: User, incoming: Incoming) -> OnboardingReply:
    guess = incoming.location
    neighborhood = guess.neighborhood if guess and guess.neighborhood else (incoming.text or "").strip()
    if not neighborhood:
        return OnboardingReply(messages.MSG_ASK_NEIGHBORHOOD_AGAIN)

    user.neighborhood = neighborhood
    return _finish(user)


ONBOARDING_TRANSITIONS: dict[OnboardingStep, Callable[[User, Incoming], OnboardingReply]] = {
    OnboardingStep.AWAITING_CONTACT: _handle_awaiting_contact,
    OnboardingStep.AWAITING_CITY: _handle_awaiting_city,
    OnboardingStep.AWAITING_NEIGHBORHOOD: _handle_awaiting_neighborhood,
}


def reset_user(user: User) -> None:
    """Volta o usuário para o início do onboarding (usado por /start)."""
    user.onboarding_step = OnboardingStep.AWAITING_CONTACT
    user.name = None
    user.phone = None
    user.city = None
    user.uf = None
    user.region = None
    user.neighborhood = None
