"""Formatador determinístico usado quando não há LLM configurado ou ele falha.

É o caminho que os testes exercitam — sem depender de rede ou de LLM.
"""

from collections.abc import Iterable
from datetime import date

from app.agent.retrieval import RetrievedContext
from app.db.models import HealthUnit, ServiceGuide
from app.messages import NO_MATCH_MESSAGE


def _format_br_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _format_source_line(source: str, updated_at: date) -> str:
    return f"Fonte: {source} · atualizado em {_format_br_date(updated_at)}"


def _format_unit(unit: HealthUnit) -> str:
    lines = [f"{unit.name} ({unit.kind}) — {unit.neighborhood or unit.city}"]
    if unit.address:
        lines.append(unit.address)
    if unit.scheduling:
        lines.append(unit.scheduling)
    if unit.opening_hours:
        lines.append(f"Horário: {unit.opening_hours}")
    if unit.accessibility:
        lines.append(f"Acessibilidade: {unit.accessibility}")
    return "\n".join(lines)


def _format_guide(guide: ServiceGuide) -> str:
    lines = [guide.how_to]
    if guide.documents:
        lines.append("Documentos necessários: " + ", ".join(guide.documents) + ".")
    return "\n".join(lines)


def format_sources(records: Iterable[HealthUnit | ServiceGuide]) -> str:
    """Uma linha "Fonte: … · atualizado em …" por par distinto de fonte e data."""
    lines = dict.fromkeys(_format_source_line(record.source, record.updated_at) for record in records)
    return "\n".join(lines)


def format_fallback_answer(context: RetrievedContext) -> str:
    if not context.units and not context.guides:
        return NO_MATCH_MESSAGE

    blocks = [_format_unit(unit) for unit in context.units]
    blocks.extend(_format_guide(guide) for guide in context.guides)
    blocks.append(format_sources([*context.units, *context.guides]))
    return "\n\n".join(blocks)
