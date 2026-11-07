"""Busca estruturada (não vetorial) de unidades e guias para uma pergunta do usuário.

Nunca toca a tabela suggestions — sugestões pending/rejected simplesmente não
têm como entrar numa resposta, porque este módulo não as consulta.
"""

from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HealthUnit, ServiceGuide
from app.domain.enums import Service
from app.domain.text import normalize_city


@dataclass(frozen=True)
class RetrievedContext:
    covered: bool
    units: list[HealthUnit]
    guides: list[ServiceGuide]


async def fetch_context(
    session: AsyncSession,
    city: str,
    uf: str,
    neighborhood: str | None,
    service: Service | None,
    max_units: int,
) -> RetrievedContext:
    city_key = normalize_city(city)

    has_coverage = await session.scalar(
        select(
            exists().where(HealthUnit.city_normalized == city_key, HealthUnit.uf == uf)
        )
    )
    if not has_coverage:
        return RetrievedContext(covered=False, units=[], guides=[])

    units_query = select(HealthUnit).where(
        HealthUnit.city_normalized == city_key,
        HealthUnit.uf == uf,
    )
    if service is not None:
        units_query = units_query.where(HealthUnit.services.contains([service.value]))

    result = await session.execute(units_query.order_by(HealthUnit.id))
    units = list(result.scalars().all())
    if neighborhood:
        home = normalize_city(neighborhood)
        units.sort(key=lambda unit: normalize_city(unit.neighborhood or "") != home)
    units = units[:max_units]

    guides_query = select(ServiceGuide).where(
        ServiceGuide.city_normalized == city_key,
        ServiceGuide.uf == uf,
    )
    if service is not None:
        guides_query = guides_query.where(ServiceGuide.service == service)
    guides_result = await session.execute(guides_query.order_by(ServiceGuide.id))

    return RetrievedContext(covered=True, units=units, guides=list(guides_result.scalars().all()))
