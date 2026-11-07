from datetime import date

from app.agent.fallback import format_fallback_answer
from app.agent.retrieval import RetrievedContext
from app.db.models import HealthUnit, ServiceGuide
from app.domain.enums import Service


def _unit(**overrides) -> HealthUnit:
    defaults = {
        "external_key": "unit-1",
        "name": "UBS Exemplo Boa Viagem",
        "kind": "UBS",
        "city": "Recife",
        "city_normalized": "recife",
        "uf": "PE",
        "neighborhood": "Boa Viagem",
        "address": "Endereço de exemplo",
        "services": ["vacinacao", "consulta"],
        "opening_hours": "Seg a sex, 7h às 17h",
        "accessibility": None,
        "scheduling": "Ordem de chegada",
        "source": "Dados de exemplo",
        "source_url": None,
        "updated_at": date(2026, 11, 1),
    }
    defaults.update(overrides)
    return HealthUnit(**defaults)


def _guide(**overrides) -> ServiceGuide:
    defaults = {
        "external_key": "guide-1",
        "city": "Recife",
        "city_normalized": "recife",
        "uf": "PE",
        "service": Service.VACINACAO,
        "how_to": "Procure a UBS do seu bairro, sem agendamento.",
        "documents": ["documento com foto", "Cartão SUS"],
        "source": "Dados de exemplo",
        "source_url": None,
        "updated_at": date(2026, 11, 1),
    }
    defaults.update(overrides)
    return ServiceGuide(**defaults)


def test_format_fallback_answer_includes_unit_and_source_line() -> None:
    context = RetrievedContext(covered=True, units=[_unit()], guide=None)

    text = format_fallback_answer(context)

    assert "UBS Exemplo Boa Viagem" in text
    assert "Fonte: Dados de exemplo · atualizado em 01/11/2026" in text


def test_format_fallback_answer_includes_guide_documents() -> None:
    context = RetrievedContext(covered=True, units=[_unit()], guide=_guide())

    text = format_fallback_answer(context)

    assert "Cartão SUS" in text
    assert "caderneta" not in text  # não inventa documento que não está no guia


def test_format_fallback_answer_deduplicates_identical_sources() -> None:
    context = RetrievedContext(covered=True, units=[_unit()], guide=_guide())

    text = format_fallback_answer(context)

    assert text.count("Fonte: Dados de exemplo") == 1


def test_format_fallback_answer_with_no_units_or_guide_says_no_match() -> None:
    context = RetrievedContext(covered=True, units=[], guide=None)

    text = format_fallback_answer(context)

    assert "Fonte" not in text
