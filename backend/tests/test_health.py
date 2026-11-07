import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.routes import health as health_route
from app.db.session import engine
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def test_health_returns_ok_when_database_is_connected(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


async def test_health_reports_disconnected_database(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def disconnected() -> bool:
        return False

    monkeypatch.setattr(health_route, "database_is_connected", disconnected)

    response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "disconnected"}


async def test_vector_extension_is_installed() -> None:
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        assert result.scalar_one() is True
