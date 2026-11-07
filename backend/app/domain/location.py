"""Parsing de "cidade, UF" nos formatos aceitos no onboarding."""

import re

from app.domain.regions import UF_TO_REGION

_SEPARATORS = re.compile(r"[,/\-]")


def parse_city_uf(raw: str) -> tuple[str, str] | None:
    """Aceita "Recife, PE", "Recife - PE", "recife pe" ou "Recife/PE".

    Retorna (cidade, UF) com a UF em caixa alta, ou None se o formato ou a UF forem inválidos.
    """
    text = raw.strip()
    if not text:
        return None

    parts = _SEPARATORS.split(text)
    if len(parts) >= 2:
        city = parts[0].strip()
        uf_candidate = parts[-1].strip().upper()
    else:
        tokens = text.split()
        if len(tokens) < 2:
            return None
        city = " ".join(tokens[:-1]).strip()
        uf_candidate = tokens[-1].strip().upper()

    if not city or uf_candidate not in UF_TO_REGION:
        return None

    return city, uf_candidate
