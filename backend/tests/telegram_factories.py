"""Monta dicts de Update do Telegram no formato que handle_update espera."""


def text_update(chat_id: int, text: str, update_id: int = 1) -> dict:
    return {"update_id": update_id, "message": {"chat": {"id": chat_id}, "text": text}}


def contact_update(
    chat_id: int,
    phone: str,
    first_name: str,
    last_name: str | None = None,
    user_id: int | None = None,
    update_id: int = 1,
) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "chat": {"id": chat_id},
            "contact": {
                "phone_number": phone,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": chat_id if user_id is None else user_id,
            },
        },
    }
