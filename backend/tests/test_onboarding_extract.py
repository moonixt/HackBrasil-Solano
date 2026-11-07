from app.domain.location import LocationGuess, guess_location
from app.onboarding.extract import parse_llm_location


def test_parse_llm_location_reads_fields() -> None:
    raw = '{"cidade": "Recife", "uf": "pe", "bairro": "Boa Viagem"}'
    assert parse_llm_location(raw) == LocationGuess("Recife", "PE", "Boa Viagem")


def test_parse_llm_location_drops_an_invented_uf() -> None:
    assert parse_llm_location('{"cidade": "Recife", "uf": "XX", "bairro": null}') == LocationGuess("Recife", None)


def test_parse_llm_location_with_nothing_found_is_none() -> None:
    assert parse_llm_location('{"cidade": null, "uf": null, "bairro": null}') is None


def test_parse_llm_location_tolerates_text_around_the_json_and_rejects_garbage() -> None:
    assert parse_llm_location('Claro! {"cidade": null, "uf": "SP", "bairro": null}') == LocationGuess(None, "SP")
    assert parse_llm_location("não sei") is None


def test_guess_location_without_llm() -> None:
    assert guess_location("Recife, PE, Boa Viagem") == LocationGuess("Recife", "PE", "Boa Viagem")
    assert guess_location("recife pe") == LocationGuess("recife", "PE")
    assert guess_location("sp") == LocationGuess(None, "SP")
    assert guess_location("Campinas") == LocationGuess("Campinas", None)
