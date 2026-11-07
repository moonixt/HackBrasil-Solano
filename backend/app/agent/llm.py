"""Escolhe o LLM configurado (Claude, senão Groq) e isola falhas de rede e de API."""

import logging

import anthropic
import httpx

from app.agent.claude import call_claude
from app.agent.groq import call_groq
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def llm_configured() -> bool:
    settings = get_settings()
    return bool(settings.anthropic_api_key or settings.groq_api_key)


async def complete(system_prompt: str, user_text: str, *, json_mode: bool = False) -> str | None:
    """Texto gerado pelo LLM, ou None quando não há LLM ou a chamada falhou."""
    settings = get_settings()
    try:
        if settings.anthropic_api_key:
            return await call_claude(
                settings.anthropic_api_key, settings.anthropic_model, system_prompt, user_text
            )
        if settings.groq_api_key:
            return await call_groq(
                settings.groq_api_key, settings.groq_model, system_prompt, user_text, json_mode=json_mode
            )
    except (anthropic.APIError, httpx.HTTPError) as exc:
        logger.warning("LLM indisponível: %s", type(exc).__name__)
    return None
