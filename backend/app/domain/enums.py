from enum import StrEnum


class SuggestionStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Service(StrEnum):
    """Serviços de saúde reconhecidos pelo agente. MVP cobre vacinação e consulta."""

    VACINACAO = "vacinacao"
    CONSULTA = "consulta"
