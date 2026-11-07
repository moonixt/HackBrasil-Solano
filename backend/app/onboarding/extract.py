"""Extração de cidade, UF e bairro por LLM, para mensagens fora do formato "Cidade, UF"."""

import json

from app.agent.llm import complete, llm_configured
from app.domain.location import LocationGuess, guess_location
from app.domain.regions import UF_TO_REGION

_PROMPT = (
    "Extraia de onde a pessoa fala, a partir de uma mensagem enviada a um bot de saúde no Brasil. "
    'Responda só com JSON: {"cidade": string|null, "uf": string|null, "bairro": string|null}.\n'
    "- uf é a sigla do estado com 2 letras. Se a cidade for conhecida e o estado não foi dito, preencha a uf.\n"
    "- Se a pessoa disse só o estado (ex.: \"sp\", \"bahia\"), cidade=null.\n"
    "- bairro é o bairro, se aparecer (ex.: \"recife, boa viagem\" → bairro \"Boa Viagem\").\n"
    "- Escreva nomes com a grafia e os acentos corretos.\n"
    "- Não invente: o que não estiver na mensagem fica null."
)


def _text_or_none(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def parse_llm_location(raw: str) -> LocationGuess | None:
    """Valida o JSON do LLM. UF fora da lista de 27 vira None, para o modelo não inventar estado."""
    try:
        data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    uf = _text_or_none(data.get("uf"))
    uf = uf.upper() if uf and uf.upper() in UF_TO_REGION else None
    guess = LocationGuess(
        city=_text_or_none(data.get("cidade")),
        uf=uf,
        neighborhood=_text_or_none(data.get("bairro")),
    )
    if guess.city is None and guess.uf is None and guess.neighborhood is None:
        return None
    return guess


async def locate(text: str, context: str | None = None) -> LocationGuess | None:
    """Cidade e UF já explícitas dispensam o LLM. Fora disso, vale o que o LLM entendeu, inclusive
    "nada"; a leitura sem LLM só entra quando não há LLM ou ele falhou.

    `context` diz ao LLM o que a mensagem responde (ex.: o bairro numa cidade já conhecida).
    """
    quick = guess_location(text)
    if quick is not None and quick.city and quick.uf:
        return quick
    if llm_configured():
        raw = await complete(_PROMPT, f"({context}) {text}" if context else text, json_mode=True)
        if raw:
            return parse_llm_location(raw)
    return quick
