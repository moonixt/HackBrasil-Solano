from enum import StrEnum


class OnboardingStep(StrEnum):
    AWAITING_CONTACT = "awaiting_contact"
    AWAITING_CITY = "awaiting_city"
    AWAITING_NEIGHBORHOOD = "awaiting_neighborhood"
    READY = "ready"


class SuggestionStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Service(StrEnum):
    """Serviços de saúde reconhecidos pelo agente. MVP cobre vacinação e consulta."""

    VACINACAO = "vacinacao"
    CONSULTA = "consulta"
