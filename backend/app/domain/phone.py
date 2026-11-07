"""Normalização de telefone brasileiro para E.164."""

import re

_MIN_DDD = 11
_MAX_DDD = 99


def normalize_br_phone(raw: str) -> str | None:
    """Aceita "5581999998888", "+55 81 99999-8888" ou o número nacional (10-11 dígitos).

    Retorna "+55DDDNUMERO" ou None quando o telefone não é um número brasileiro válido.
    """
    digits = re.sub(r"\D", "", raw)

    if raw.strip().startswith("+") and not digits.startswith("55"):
        return None  # "+" com DDI diferente de 55 não é suportado (MVP só atende o Brasil)

    if digits.startswith("55") and len(digits) in (12, 13):
        national = digits[2:]
    elif len(digits) in (10, 11):
        national = digits
    else:
        return None

    ddd, subscriber = national[:2], national[2:]
    if len(subscriber) not in (8, 9):
        return None
    if not (_MIN_DDD <= int(ddd) <= _MAX_DDD):
        return None

    return f"+55{ddd}{subscriber}"
