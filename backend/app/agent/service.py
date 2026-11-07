"""Orquestra a resposta: gate de emergência → busca estruturada → LLM (Claude ou Groq) ou fallback."""

import logging
from dataclasses import replace

import anthropic
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.claude import call_claude
from app.agent.fallback import format_fallback_answer, format_sources
from app.agent.groq import call_groq
from app.agent.keywords import detect_service, is_emergency
from app.agent.prompts import SOURCES_MARKER, build_system_prompt
from app.agent.retrieval import RetrievedContext, fetch_context
from app.core.config import get_settings
from app.db.models import User
from app.domain.regions import Region
from app.onboarding.messages import EMERGENCY_REPLY, NOT_COVERED_MESSAGE

logger = logging.getLogger(__name__)

# O fallback mostra poucas unidades; o LLM recebe mais para responder perguntas abertas.
_FALLBACK_UNITS = 3
_LLM_UNITS = 20


def _llm_configured() -> bool:
    settings = get_settings()
    return bool(settings.anthropic_api_key or settings.groq_api_key)


def _bullet(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith(("* ", "- ")):
        return "• " + stripped[2:]
    return line


def _clean_reply(reply: str, context: RetrievedContext) -> str:
    """Texto simples para o Telegram, com as fontes reais no lugar do marcador.

    O Telegram (sem parse_mode) mostra markdown como texto cru, e o modelo nem sempre
    obedece ao pedido de não usar; linhas de fonte escritas pelo modelo são descartadas.
    """
    kept = [
        _bullet(line.replace("**", ""))
        for line in reply.splitlines()
        if not line.strip().casefold().startswith("fonte")
    ]
    text = "\n".join(kept).strip()
    if SOURCES_MARKER not in text:
        return text
    return text.replace(SOURCES_MARKER, format_sources(context)).strip()


async def _llm_reply(region: Region, context: RetrievedContext, question: str) -> str | None:
    settings = get_settings()
    system_prompt = build_system_prompt(region, context)
    try:
        if settings.anthropic_api_key:
            return await call_claude(
                settings.anthropic_api_key, settings.anthropic_model, system_prompt, question
            )
        if settings.groq_api_key:
            return await call_groq(settings.groq_api_key, settings.groq_model, system_prompt, question)
    except (anthropic.APIError, httpx.HTTPError) as exc:
        logger.warning("LLM indisponível, usando a resposta a partir dos dados: %s", type(exc).__name__)
    return None


async def answer(session: AsyncSession, user: User, question: str) -> str:
    if is_emergency(question):
        return EMERGENCY_REPLY

    service = detect_service(question)
    use_llm = _llm_configured()
    context = await fetch_context(session, user, service, _LLM_UNITS if use_llm else _FALLBACK_UNITS)
    if not context.covered:
        return NOT_COVERED_MESSAGE.format(city=user.city, uf=user.uf)

    if use_llm:
        reply = await _llm_reply(user.region, context, question)
        if reply and reply.strip():
            return _clean_reply(reply, context)
        context = replace(context, units=context.units[:_FALLBACK_UNITS])
    return format_fallback_answer(context)
