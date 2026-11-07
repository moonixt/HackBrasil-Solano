"""Ferramentas do agente: o nome que o LLM chama → esquema (formato OpenAI) + implementação.

Os argumentos vêm do LLM, então são validados aqui, na borda: UF fora das 27, serviço
desconhecido ou localização ausente viram um {"erro": ...} que o próprio modelo lê e corrige.
"""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.personas import REGIONAL_AGENTS
from app.agent.retrieval import fetch_context
from app.core.config import get_settings
from app.db.models import HealthUnit, ServiceGuide, Suggestion, User
from app.domain.enums import Service
from app.domain.regions import UF_TO_REGION

_MAX_UNITS = 20


@dataclass
class ToolContext:
    session: AsyncSession
    user: User
    # Registros devolvidos ao LLM nesta resposta: viram as linhas de fonte.
    records: list[HealthUnit | ServiceGuide] = field(default_factory=list)


@dataclass(frozen=True)
class Tool:
    schema: dict[str, Any]
    run: Callable[[ToolContext, dict[str, Any]], Awaitable[dict[str, Any]]]


def _text(args: dict[str, Any], key: str) -> str | None:
    value = args.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def set_location(user: User, city: str, uf: str, neighborhood: str | None) -> None:
    user.city = city
    user.uf = uf
    user.region = UF_TO_REGION[uf]
    user.neighborhood = neighborhood


async def _save_location(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    city, uf = _text(args, "cidade"), (_text(args, "uf") or "").upper()
    if city is None or uf not in UF_TO_REGION:
        return {"erro": "informe cidade e uma UF válida (sigla de 2 letras)"}
    set_location(ctx.user, city, uf, _text(args, "bairro"))
    await ctx.session.flush()
    return {"salvo": True, "agente": REGIONAL_AGENTS[UF_TO_REGION[uf]].name}


def _compact(record: dict[str, Any]) -> dict[str, Any]:
    """Sem campos vazios: cada token conta no limite por minuto do LLM."""
    return {key: value for key, value in record.items() if value not in (None, "", [])}


def _unit_record(unit: HealthUnit) -> dict[str, Any]:
    return _compact({
        "nome": unit.name,
        "tipo": unit.kind,
        "bairro": unit.neighborhood,
        "endereco": unit.address,
        "servicos": unit.services,
        "horario": unit.opening_hours,
        "acessibilidade": unit.accessibility,
        "como_agendar": unit.scheduling,
        "atualizado_em": unit.updated_at.isoformat(),
    })


def _guide_record(guide: ServiceGuide) -> dict[str, Any]:
    return _compact({
        "servico": guide.service.value,
        "como_fazer": guide.how_to,
        "documentos": guide.documents,
        "atualizado_em": guide.updated_at.isoformat(),
    })


async def _search_network(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    user = ctx.user
    city = _text(args, "cidade") or user.city
    uf = (_text(args, "uf") or user.uf or "").upper()
    if city is None or uf not in UF_TO_REGION:
        return {"erro": "localização desconhecida: pergunte a cidade e o estado da pessoa"}
    service_name = _text(args, "servico")
    service = Service(service_name) if service_name in set(Service) else None
    neighborhood = _text(args, "bairro") or (user.neighborhood if city == user.city else None)

    context = await fetch_context(ctx.session, city, uf, neighborhood, service, _MAX_UNITS)
    if not context.covered:
        return {"cidade_tem_dados": False, "cidade": city, "uf": uf}
    ctx.records.extend([*context.units, *context.guides])
    return {
        "cidade_tem_dados": True,
        "unidades": [_unit_record(unit) for unit in context.units],
        "guias": [_guide_record(guide) for guide in context.guides],
    }


async def _register_suggestion(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    text = _text(args, "texto")
    user = ctx.user
    if text is None:
        return {"erro": "texto da sugestão vazio"}
    if user.city is None or user.uf is None:
        return {"erro": "salve a localização da pessoa antes de registrar a sugestão"}
    ctx.session.add(Suggestion(user_id=user.id, city=user.city, uf=user.uf, text=text))
    await ctx.session.flush()
    return {"registrada": True, "status": "pendente de verificação"}


def _function(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOLS: dict[str, Tool] = {
    "salvar_localizacao": Tool(
        _function(
            "salvar_localizacao",
            "Salva onde a pessoa mora ou está. Chame quando ela disser a cidade (e o bairro, se disser).",
            {
                "cidade": {"type": "string"},
                "uf": {"type": "string", "description": "Sigla do estado, 2 letras"},
                "bairro": {"type": ["string", "null"]},
            },
            ["cidade", "uf"],
        ),
        _save_location,
    ),
    "buscar_rede_de_saude": Tool(
        _function(
            "buscar_rede_de_saude",
            "Busca unidades de saúde (endereço, horário, acessibilidade, como agendar) e guias de "
            "serviço (como fazer, documentos) de uma cidade. Sem cidade, usa a localização salva.",
            {
                "cidade": {"type": ["string", "null"]},
                "uf": {"type": ["string", "null"]},
                "bairro": {"type": ["string", "null"]},
                "servico": {"type": ["string", "null"], "enum": [*[s.value for s in Service], None]},
            },
            [],
        ),
        _search_network,
    ),
    "registrar_sugestao": Tool(
        _function(
            "registrar_sugestao",
            "Registra uma correção ou informação nova sobre uma unidade, enviada pela pessoa. "
            "Fica pendente de verificação e não é usada nas respostas até ser verificada.",
            {"texto": {"type": "string"}},
            ["texto"],
        ),
        _register_suggestion,
    ),
}

TOOL_SCHEMAS = [tool.schema for tool in TOOLS.values()]
# Busca na web executada pelo próprio provedor (Groq, modelos gpt-oss): não passa por run_tool.
_WEB_SEARCH = {"type": "browser_search"}


def agent_tools() -> list[dict[str, Any]]:
    return [*TOOL_SCHEMAS, _WEB_SEARCH] if get_settings().llm_web_search else TOOL_SCHEMAS


async def run_tool(ctx: ToolContext, name: str, raw_arguments: str | None) -> dict[str, Any]:
    tool = TOOLS.get(name)
    if tool is None:
        return {"erro": f"ferramenta desconhecida: {name}"}
    try:
        args = json.loads(raw_arguments or "{}")
    except ValueError:
        return {"erro": "argumentos em JSON inválido"}
    return await tool.run(ctx, args if isinstance(args, dict) else {})
