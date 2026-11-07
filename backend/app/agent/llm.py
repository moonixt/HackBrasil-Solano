"""Cliente do LLM por API compatível com a da OpenAI (Groq por padrão), com tools."""

import asyncio
import logging
import re
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_MAX_TOKENS = 600
# Plano gratuito da Groq: 8.000 tokens/minuto. Num 429, espera o que a API pedir (até este teto) e tenta uma vez.
_MAX_RATE_LIMIT_WAIT = 20.0


def llm_configured() -> bool:
    return bool(get_settings().llm_api_key)


async def chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Uma rodada de chat completions. Devolve a mensagem do assistente, ou None se a chamada falhou."""
    settings = get_settings()
    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "max_completion_tokens": _MAX_TOKENS,
        "temperature": 0.3,
        "reasoning_effort": "low",
    }
    if tools:
        payload["tools"] = tools
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    url = f"{settings.llm_base_url}/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 429:
                wait = _retry_after(response)
                if wait is None:
                    response.raise_for_status()
                logger.info("LLM no limite de taxa, esperando %.1fs", wait)
                await asyncio.sleep(wait)
                response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("LLM indisponível: %s", type(exc).__name__)
        return None
    return response.json()["choices"][0]["message"]


def _seconds(value: str | None) -> float:
    """"7.56s", "1m2.5s" ou "3" → segundos; o que não der para ler vale 0."""
    match = re.fullmatch(r"(?:(\d+)m)?([\d.]+)s?", (value or "").strip())
    if match is None:
        return 0.0
    return int(match.group(1) or 0) * 60 + float(match.group(2))


def _retry_after(response: httpx.Response) -> float | None:
    # A Groq manda retry-after curto, mas o limite de tokens só libera em x-ratelimit-reset-tokens.
    wait = max(
        _seconds(response.headers.get("retry-after")),
        _seconds(response.headers.get("x-ratelimit-reset-tokens")),
    )
    return wait if 0 < wait <= _MAX_RATE_LIMIT_WAIT else None
