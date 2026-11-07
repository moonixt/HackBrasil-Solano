"""Busca estruturada (não vetorial) de unidades e guias para uma pergunta do usuário.

Nunca toca a tabela suggestions — sugestões pending/rejected simplesmente não
têm como entrar numa resposta, porque este módulo não as consulta.
"""

from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HealthUnit, ServiceGuide, User
from app.domain.enums import Service
from app.domain.text import normalize_city

_MAX_UNITS = 3


@dataclass(frozen=True)
class RetrievedContext:
    covered: bool
    units: list[HealthUnit]
    guide: ServiceGuide | None


async def fetch_context(session: AsyncSession, user: User, service: Service | None) -> RetrievedContext:
    if user.city is None or user.uf is None:
        return RetrievedContext(covered=False, units=[], guide=None)

    city_key = normalize_city(user.city)

    has_coverage = await session.scalar(
        select(
            exists().where(HealthUnit.city_normalized == city_key, HealthUnit.uf == user.uf)
        )
    )
    if not has_coverage:
        return RetrievedContext(covered=False, units=[], guide=None)

    units_query = select(HealthUnit).where(
        HealthUnit.city_normalized == city_key,
        HealthUnit.uf == user.uf,
    )
    if service is not None:
        units_query = units_query.where(HealthUnit.services.any(service.value))

    neighborhood = user.neighborhood
    result = await session.execute(units_query.order_by(HealthUnit.id))
    units = list(result.scalars().all())
    if neighborhood:
        units.sort(key=lambda unit: unit.neighborhood != neighborhood)
    units = units[:_MAX_UNITS]

    guide: ServiceGuide | None = None
    if service is not None:
        guide_result = await session.execute(
            select(ServiceGuide)
            .where(
                ServiceGuide.city_normalized == city_key,
                ServiceGuide.uf == user.uf,
                ServiceGuide.service == service,
            )
            .limit(1)
        )
        guide = guide_result.scalar_one_or_none()

    return RetrievedContext(covered=True, units=units, guide=guide)
