"""O agente do Solano: toda mensagem passa por aqui.

Gate de emergência (determinístico) → LLM com ferramentas, em poucas rodadas → texto
limpo para o Telegram com as fontes reais. Sem LLM (ou se ele falhar), responde pelos
dados com o formatador determinístico.
"""

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import memory
from app.agent.fallback import format_fallback_answer, format_sources
from app.agent.keywords import detect_service, is_emergency
from app.agent.llm import chat, llm_configured
from app.agent.personas import REGIONAL_AGENTS
from app.agent.retrieval import fetch_context
from app.agent.tools import ToolContext, agent_tools, run_tool, set_location
from app.db.models import HealthUnit, ServiceGuide, User
from app.domain.location import guess_location
from app import messages

SOURCES_MARKER = "[FONTES]"
# Caracteres de largura zero que o modelo às vezes emite em sequência.
_INVISIBLE = re.compile("[\u200b-\u200f\u2060\ufeff]")
# Marcas de citação do gpt-oss, como 【0†L4-L5】.
_CITATION = re.compile("[ \t]*【[^】]*】")
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_RESULT_DOMAIN = re.compile("†([a-z0-9.-]+\\.[a-z]{2,})】", re.IGNORECASE)
_URL_DOMAIN = re.compile(r"https?://([a-z0-9.-]+\.[a-z]{2,})", re.IGNORECASE)
_SEARCH_ENGINES = {"exa.ai"}
_MAX_ROUNDS = 4
_FALLBACK_UNITS = 3

_RULES = f"""\
Você conversa no Telegram e orienta pessoas sobre a rede pública de saúde (SUS) no Brasil:
onde se vacinar, como marcar consulta na UBS, que documentos levar, horários e acessibilidade.

Como agir:
- Responda direto ao que a pessoa perguntou, como numa conversa. Não faça cadastro nem peça dados sem necessidade.
- Sempre que a pessoa disser onde mora ou está (cidade, estado ou bairro), chame salvar_localizacao
  na hora e confirme em uma frase curta qual agente regional vai acompanhá-la.
- Para qualquer informação local (unidades, endereços, horários, como agendar, documentos), chame
  buscar_rede_de_saude e use só o que ela devolver. Se precisar da localização e ela for desconhecida,
  pergunte a cidade e o bairro.
- Se a cidade não tiver dados no Solano (ou faltar a informação pedida) e você tiver busca na web, pesquise.
  Prefira sites oficiais (prefeitura, secretaria de saúde, gov.br). Diga que a informação veio da internet
  e que é bom confirmar na unidade. Termine com uma linha "Fonte: <site> (<endereço>) · <data da publicação,
  se houver>" para cada página que você realmente usou.
- Sem dados e sem resultado na web, diga isso com franqueza e dê só a orientação geral do SUS (procurar a UBS
  mais próxima com documento com foto e Cartão SUS ou CPF; Disque Saúde 136), deixando claro que é geral.
- Nunca invente nome de unidade, endereço, telefone ou horário.
- Nunca faça diagnóstico, não interprete sintomas, não indique remédio nem dose. Em sinais de urgência,
  mande ligar 192 (SAMU) ou ir à UPA.
- Se a pessoa corrigir ou acrescentar algo sobre uma unidade, chame registrar_sugestao e explique que
  fica pendente até ser verificada.
- Se usar dados de buscar_rede_de_saude, termine com uma linha contendo só {SOURCES_MARKER}
  (o sistema troca pela fonte certa). Para esses dados, não escreva a fonte você mesmo.
- Fora de saúde pública, diga com gentileza que só ajuda com isso.
- Texto simples e curto, sem markdown (nada de asteriscos, # ou tabelas)."""


def build_system_prompt(user: User) -> str:
    if user.region is not None:
        persona = REGIONAL_AGENTS[user.region]
        who = f"Você é o Solano, {persona.name}, com tom {persona.tone}."
    else:
        who = "Você é o Solano, com tom acolhedor e direto."
    if user.city and user.uf:
        place = f"{user.city}/{user.uf}" + (f", bairro {user.neighborhood}" if user.neighborhood else "")
    else:
        place = "ainda não informada"
    return f"{who}\n{_RULES}\n\nLocalização salva da pessoa: {place}."


def _bullet(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith(("* ", "- ")):
        return "• " + stripped[2:]
    return line


def _plain_lines(reply: str) -> list[str]:
    """Markdown → texto simples: sem negrito, listas viram "•", tabelas viram uma linha por registro."""
    lines: list[str] = []
    in_table = False
    for line in reply.splitlines():
        if _TABLE_ROW.match(line):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            # A primeira linha da tabela é o cabeçalho; a de traços é o separador.
            if in_table and not all(set(cell) <= set("-: ") for cell in cells):
                lines.append("• " + " – ".join(cell for cell in cells if cell))
            in_table = True
            continue
        in_table = False
        lines.append(_bullet(line.replace("**", "")))
    return lines


def web_domains(reply: dict[str, Any]) -> set[str]:
    """Sites que a busca na web do provedor devolveu nesta rodada (Groq: executed_tools)."""
    domains: set[str] = set()
    for executed in reply.get("executed_tools") or []:
        output = str(executed.get("output") or "")
        domains.update(_RESULT_DOMAIN.findall(output))
        domains.update(_URL_DOMAIN.findall(output))
    return {domain.removeprefix("www.").lower() for domain in domains} - _SEARCH_ENGINES


def clean_reply(
    reply: str, records: list[HealthUnit | ServiceGuide], searched_domains: set[str] = frozenset()
) -> str:
    """Texto simples para o Telegram, com fontes que dá para confirmar.

    Fontes dos dados do Solano entram pelo marcador. Uma linha de fonte escrita pelo modelo
    só fica se citar um site que a busca na web realmente devolveu nesta resposta.
    """
    reply = _CITATION.sub("", _INVISIBLE.sub("", reply))
    kept = []
    for line in _plain_lines(reply):
        if line.strip().casefold().startswith(("fonte", "• fonte")):
            if not any(domain in line.casefold() for domain in searched_domains):
                continue
        kept.append(line.rstrip())
    text = "\n".join(kept).strip()
    if SOURCES_MARKER not in text:
        return text
    return text.replace(SOURCES_MARKER, format_sources(records) if records else "").strip()


async def _agent_reply(session: AsyncSession, user: User, text: str) -> str | None:
    ctx = ToolContext(session=session, user=user)
    conversation: list[dict[str, Any]] = [
        {"role": "system", "content": build_system_prompt(user)},
        *memory.history(user.telegram_chat_id),
        {"role": "user", "content": text},
    ]
    searched_domains: set[str] = set()
    for _ in range(_MAX_ROUNDS):
        reply = await chat(conversation, agent_tools())
        if reply is None:
            return None
        searched_domains |= web_domains(reply)
        calls = reply.get("tool_calls") or []
        if not calls:
            answer = clean_reply(reply.get("content") or "", ctx.records, searched_domains)
            return answer or None
        conversation.append({"role": "assistant", "content": reply.get("content") or "", "tool_calls": calls})
        for call in calls:
            result = await run_tool(ctx, call["function"]["name"], call["function"].get("arguments"))
            conversation.append(
                {"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, ensure_ascii=False)}
            )
    return None


async def _fallback_reply(session: AsyncSession, user: User, text: str) -> str:
    if user.city is None or user.uf is None:
        guess = guess_location(text)
        if guess is None or guess.city is None or guess.uf is None:
            return messages.MSG_ASK_LOCATION
        set_location(user, guess.city, guess.uf, guess.neighborhood)
        return messages.MSG_LOCATION_SAVED.format(agent_name=REGIONAL_AGENTS[user.region].name)

    service = detect_service(text)
    context = await fetch_context(session, user.city, user.uf, user.neighborhood, service, _FALLBACK_UNITS)
    if not context.covered:
        return messages.NOT_COVERED_MESSAGE.format(city=user.city, uf=user.uf)
    return format_fallback_answer(context)


async def respond(session: AsyncSession, user: User, text: str) -> str:
    if is_emergency(text):
        return messages.EMERGENCY_REPLY

    answer = await _agent_reply(session, user, text) if llm_configured() else None
    if answer is None:
        answer = await _fallback_reply(session, user, text)
    memory.remember(
        user.telegram_chat_id,
        {"role": "user", "content": text},
        {"role": "assistant", "content": answer},
    )
    return answer
