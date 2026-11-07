from app.domain.location import parse_city_uf
from app.domain.phone import normalize_br_phone
from app.domain.regions import UF_TO_REGION, Region
from app.domain.text import normalize_city


def test_uf_to_region_covers_all_27_ufs_in_the_five_regions() -> None:
    assert len(UF_TO_REGION) == 27
    assert set(UF_TO_REGION.values()) == set(Region)


def test_normalize_br_phone_accepts_full_e164_digits() -> None:
    assert normalize_br_phone("5581999998888") == "+5581999998888"


def test_normalize_br_phone_accepts_formatted_input() -> None:
    assert normalize_br_phone("+55 81 99999-8888") == "+5581999998888"


def test_normalize_br_phone_accepts_national_number_without_country_code() -> None:
    assert normalize_br_phone("81999998888") == "+5581999998888"


def test_normalize_br_phone_rejects_non_br_country_code() -> None:
    assert normalize_br_phone("+1 415 555 0100") is None


def test_normalize_br_phone_rejects_garbage() -> None:
    assert normalize_br_phone("not a phone") is None
    assert normalize_br_phone("123") is None


def test_parse_city_uf_accepts_comma_format() -> None:
    assert parse_city_uf("Recife, PE") == ("Recife", "PE")


def test_parse_city_uf_accepts_dash_format() -> None:
    assert parse_city_uf("Recife - PE") == ("Recife", "PE")


def test_parse_city_uf_accepts_space_format_lowercase() -> None:
    assert parse_city_uf("recife pe") == ("recife", "PE")


def test_parse_city_uf_accepts_slash_format() -> None:
    assert parse_city_uf("Recife/PE") == ("Recife", "PE")


def test_parse_city_uf_rejects_invalid_uf() -> None:
    assert parse_city_uf("Recife, XX") is None


def test_parse_city_uf_rejects_missing_uf() -> None:
    assert parse_city_uf("Recife") is None


def test_normalize_city_strips_accents_and_collapses_spaces() -> None:
    assert normalize_city("  São   Paulo ") == "sao paulo"
