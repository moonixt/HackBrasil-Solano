from app.agent.keywords import detect_service, is_emergency
from app.domain.enums import Service


def test_is_emergency_matches_known_phrases_regardless_of_accents() -> None:
    assert is_emergency("estou com dor no peito")
    assert is_emergency("ele teve uma convulsão")
    assert is_emergency("pensamento suicida")


def test_is_emergency_is_false_for_routine_questions() -> None:
    assert not is_emergency("onde consigo me vacinar?")
    assert not is_emergency("como marco uma consulta na UBS?")


def test_detect_service_matches_vacinacao() -> None:
    assert detect_service("onde consigo me vacinar?") == Service.VACINACAO


def test_detect_service_matches_consulta() -> None:
    assert detect_service("como marco uma consulta na UBS?") == Service.CONSULTA
    assert detect_service("quero agendar um atendimento") == Service.CONSULTA


def test_detect_service_returns_none_for_unrelated_questions() -> None:
    assert detect_service("qual o horário de funcionamento?") is None
