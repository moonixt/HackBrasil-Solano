from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import async_session_factory, engine
from app.main import app

_TABLES = ("suggestions", "service_guides", "health_units", "users")


async def _truncate_all() -> None:
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE TABLE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def _no_llm_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """O .env de quem roda os testes pode ter chaves reais; os testes nunca chamam LLM pela rede."""
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", None)


@pytest.fixture
async def _clean_db():
    """Só tocado pelos testes que pedem `session` ou `client` — os testes puros nunca
    precisam de Postgres no ar."""
    await _truncate_all()
    yield
    await _truncate_all()


@pytest.fixture
async def session(_clean_db):
    async with async_session_factory() as db_session:
        yield db_session


@pytest.fixture
async def client(_clean_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@dataclass
class SentMessage:
    chat_id: int
    text: str
    reply_markup: dict | None = None


class FakeTelegramClient:
    """Registra as mensagens enviadas em vez de chamar a Bot API de verdade."""

    def __init__(self) -> None:
        self.sent: list[SentMessage] = []

    async def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None):
        self.sent.append(SentMessage(chat_id, text, reply_markup))
        return {"ok": True, "result": {"message_id": len(self.sent)}}

    async def send_chat_action(self, chat_id: int, action: str):
        return {"ok": True, "result": True}


@pytest.fixture
def fake_telegram_client() -> FakeTelegramClient:
    return FakeTelegramClient()
