"""Leitura de "Cidade, UF" sem LLM, usada pelo fallback do agente."""

import re
from dataclasses import dataclass

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


@dataclass(frozen=True)
class LocationGuess:
    """O que deu para entender de uma mensagem sobre onde a pessoa está. Campos ausentes são None."""

    city: str | None
    uf: str | None
    neighborhood: str | None = None


def guess_location(raw: str) -> LocationGuess | None:
    """Leitura sem LLM: "Cidade, UF, Bairro", "Cidade, UF", só a UF ("sp"), ou o texto como cidade sem UF."""
    text = raw.strip()
    if not text:
        return None
    parts = [part.strip() for part in _SEPARATORS.split(text)]
    if len(parts) >= 3 and parts[0] and parts[1].upper() in UF_TO_REGION:
        neighborhood = ", ".join(part for part in parts[2:] if part) or None
        return LocationGuess(city=parts[0], uf=parts[1].upper(), neighborhood=neighborhood)
    parsed = parse_city_uf(text)
    if parsed is not None:
        return LocationGuess(city=parsed[0], uf=parsed[1])
    if text.upper() in UF_TO_REGION:
        return LocationGuess(city=None, uf=text.upper())
    return LocationGuess(city=text, uf=None)
