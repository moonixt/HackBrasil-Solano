"""Carrega unidades e guias de saúde de um JSON, com upsert idempotente por external_key.

Uso: uv run python -m app.seed data/recife_exemplo.json
"""

import asyncio
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HealthUnit, ServiceGuide
from app.db.session import async_session_factory
from app.domain.text import normalize_city

_UNIT_FIELDS = (
    "name",
    "kind",
    "city",
    "uf",
    "neighborhood",
    "address",
    "services",
    "opening_hours",
    "accessibility",
    "scheduling",
    "source",
    "source_url",
)

_GUIDE_FIELDS = ("city", "uf", "service", "how_to", "documents", "source", "source_url")


async def _upsert_unit(session: AsyncSession, payload: dict[str, Any]) -> None:
    result = await session.execute(
        select(HealthUnit).where(HealthUnit.external_key == payload["external_key"])
    )
    unit = result.scalar_one_or_none()
    if unit is None:
        unit = HealthUnit(external_key=payload["external_key"])
        session.add(unit)

    for field in _UNIT_FIELDS:
        setattr(unit, field, payload[field])
    unit.city_normalized = normalize_city(payload["city"])
    unit.updated_at = date.fromisoformat(payload["updated_at"])


async def _upsert_guide(session: AsyncSession, payload: dict[str, Any]) -> None:
    result = await session.execute(
        select(ServiceGuide).where(ServiceGuide.external_key == payload["external_key"])
    )
    guide = result.scalar_one_or_none()
    if guide is None:
        guide = ServiceGuide(external_key=payload["external_key"])
        session.add(guide)

    for field in _GUIDE_FIELDS:
        setattr(guide, field, payload[field])
    guide.city_normalized = normalize_city(payload["city"])
    guide.updated_at = date.fromisoformat(payload["updated_at"])


async def seed(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    async with async_session_factory() as session:
        for unit_payload in data.get("health_units", []):
            await _upsert_unit(session, unit_payload)
        for guide_payload in data.get("service_guides", []):
            await _upsert_guide(session, guide_payload)
        await session.commit()


def main() -> None:
    if len(sys.argv) != 2:
        print("uso: uv run python -m app.seed <arquivo.json>")
        raise SystemExit(1)
    asyncio.run(seed(Path(sys.argv[1])))


if __name__ == "__main__":
    main()
