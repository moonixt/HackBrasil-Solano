"""Formatador determinístico usado quando ANTHROPIC_API_KEY não está configurada.

É o caminho que os testes exercitam — sem depender de rede ou de LLM.
"""

from datetime import date

from app.agent.retrieval import RetrievedContext
from app.db.models import HealthUnit, ServiceGuide
from app.onboarding.messages import NO_MATCH_MESSAGE


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
    return "\n".join(lines)


def _format_guide(guide: ServiceGuide) -> str:
    lines = [guide.how_to]
    if guide.documents:
        lines.append("Documentos necessários: " + ", ".join(guide.documents) + ".")
    return "\n".join(lines)


def format_fallback_answer(context: RetrievedContext) -> str:
    guide = context.guide
    if not context.units and guide is None:
        return NO_MATCH_MESSAGE

    blocks = [_format_unit(unit) for unit in context.units]
    if guide is not None:
        blocks.append(_format_guide(guide))

    sources: dict[str, str] = {}
    for unit in context.units:
        sources[unit.source] = _format_source_line(unit.source, unit.updated_at)
    if guide is not None:
        sources[guide.source] = _format_source_line(guide.source, guide.updated_at)

    blocks.append("\n".join(sources.values()))
    return "\n\n".join(blocks)
