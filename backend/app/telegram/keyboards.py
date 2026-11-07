"""Reply keyboards da Bot API, mapeadas a partir de KeyboardAction."""

from app.onboarding.state_machine import KeyboardAction

CONTACT_KEYBOARD = {
    "keyboard": [[{"text": "Compartilhar meu telefone", "request_contact": True}]],
    "resize_keyboard": True,
    "one_time_keyboard": True,
}

REMOVE_KEYBOARD = {"remove_keyboard": True}

_MARKUP_BY_ACTION: dict[KeyboardAction, dict | None] = {
    KeyboardAction.NONE: None,
    KeyboardAction.SHOW_CONTACT: CONTACT_KEYBOARD,
    KeyboardAction.REMOVE: REMOVE_KEYBOARD,
}


def markup_for(action: KeyboardAction) -> dict | None:
    return _MARKUP_BY_ACTION[action]
