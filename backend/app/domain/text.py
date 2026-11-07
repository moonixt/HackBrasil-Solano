"""Normalização de texto compartilhada por busca de cidade e detecção de palavras-chave."""

import re
import unicodedata


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def fold(value: str) -> str:
    """Casefold + sem acentos, para comparação tolerante a maiúsculas e acentuação."""
    return strip_accents(value.casefold())


def normalize_city(value: str) -> str:
    """Chave normalizada de cidade: sem acento, minúscula, espaços únicos."""
    folded = fold(value.strip())
    return re.sub(r"\s+", " ", folded)
