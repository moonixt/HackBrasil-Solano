"""Orquestra a resposta: gate de emergência → busca estruturada → Claude ou fallback."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.claude import call_claude
from app.agent.fallback import format_fallback_answer
from app.agent.keywords import detect_service, is_emergency
from app.agent.prompts import build_system_prompt
from app.agent.retrieval import fetch_context
from app.core.config import get_settings
from app.db.models import User
from app.onboarding.messages import EMERGENCY_REPLY, NOT_COVERED_MESSAGE


async def answer(session: AsyncSession, user: User, question: str) -> str:
    if is_emergency(question):
        return EMERGENCY_REPLY

    service = detect_service(question)
    context = await fetch_context(session, user, service)
    if not context.covered:
        return NOT_COVERED_MESSAGE.format(city=user.city, uf=user.uf)

    settings = get_settings()
    if settings.anthropic_api_key:
        system_prompt = build_system_prompt(user.region, context)
        return await call_claude(settings.anthropic_api_key, settings.anthropic_model, system_prompt, question)

    return format_fallback_answer(context)
