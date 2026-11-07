"""Memória curta da conversa, só em processo: últimas mensagens por chat, descartadas após inatividade.

Nada disso vai para o banco — o Solano não guarda histórico de conversa (ver app.db.models).
"""

import time
from dataclasses import dataclass, field
from typing import Any

_MAX_MESSAGES = 20
_TTL_SECONDS = 30 * 60


@dataclass
class _Conversation:
    messages: list[dict[str, Any]] = field(default_factory=list)
    last_seen: float = 0.0


_conversations: dict[int, _Conversation] = {}


def history(chat_id: int) -> list[dict[str, Any]]:
    conversation = _conversations.get(chat_id)
    if conversation is None or time.monotonic() - conversation.last_seen > _TTL_SECONDS:
        _conversations.pop(chat_id, None)
        return []
    return list(conversation.messages)


def remember(chat_id: int, *messages: dict[str, Any]) -> None:
    conversation = _conversations.setdefault(chat_id, _Conversation())
    conversation.messages.extend(messages)
    del conversation.messages[:-_MAX_MESSAGES]
    conversation.last_seen = time.monotonic()


def forget(chat_id: int) -> None:
    _conversations.pop(chat_id, None)
