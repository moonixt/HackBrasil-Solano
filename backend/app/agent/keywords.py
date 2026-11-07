"""Gate de segurança e detecção de serviço por palavra-chave. Determinístico, sem LLM."""

from app.domain.enums import Service
from app.domain.text import fold

_EMERGENCY_KEYWORDS = (
    "dor no peito",
    "falta de ar",
    "desmaio",
    "sangramento",
    "infarto",
    "avc",
    "convulsao",
    "suicid",
)

_VACINACAO_KEYWORDS = ("vacina",)
_CONSULTA_KEYWORDS = ("consulta", "marcar", "agendar")


def is_emergency(text: str) -> bool:
    folded = fold(text)
    return any(keyword in folded for keyword in _EMERGENCY_KEYWORDS)


def detect_service(text: str) -> Service | None:
    folded = fold(text)
    if any(keyword in folded for keyword in _VACINACAO_KEYWORDS):
        return Service.VACINACAO
    if any(keyword in folded for keyword in _CONSULTA_KEYWORDS):
        return Service.CONSULTA
    return None
