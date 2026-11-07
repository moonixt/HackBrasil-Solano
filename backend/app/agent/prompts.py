"""Monta o system prompt enviado ao Claude: persona regional + escopo + registros."""

from app.agent.personas import REGIONAL_AGENTS
from app.agent.retrieval import RetrievedContext
from app.db.models import HealthUnit, ServiceGuide
from app.domain.regions import Region

SOURCES_MARKER = "[FONTES]"

_SCOPE_RULES = (
    "Seu único assunto é orientação sobre a rede pública de saúde: onde encontrar "
    "unidades, como marcar consulta, documentos necessários e serviços disponíveis.\n"
    "Nunca dê diagnóstico, nunca receite medicamento ou indique dose, e nunca invente "
    "informação: responda SOMENTE com base nos registros abaixo.\n"
    "Se os registros não cobrirem a pergunta, diga isso e sugira procurar a UBS mais "
    "próxima ou ligar no Disque Saúde 136.\n"
    f"Não escreva linhas de fonte. Se a resposta usar algum registro, termine com uma "
    f"linha contendo só {SOURCES_MARKER} — o sistema troca pela fonte e data corretas.\n"
    "Responda curto e em texto simples, sem markdown (nada de asteriscos, # ou tabelas): "
    "é uma mensagem de Telegram, não um artigo."
)


def _render_unit(unit: HealthUnit) -> str:
    parts = [f"- {unit.name} ({unit.kind}), bairro {unit.neighborhood or unit.city}"]
    if unit.address:
        parts.append(f"endereço: {unit.address}")
    if unit.services:
        parts.append(f"serviços: {', '.join(unit.services)}")
    if unit.scheduling:
        parts.append(f"como agendar: {unit.scheduling}")
    if unit.opening_hours:
        parts.append(f"horário: {unit.opening_hours}")
    if unit.accessibility:
        parts.append(f"acessibilidade: {unit.accessibility}")
    parts.append(f"fonte: {unit.source} (atualizado em {unit.updated_at.strftime('%d/%m/%Y')})")
    return "; ".join(parts)


def _render_guide(guide: ServiceGuide) -> str:
    parts = [f"- Guia de {guide.service.value}: {guide.how_to}"]
    if guide.documents:
        parts.append(f"documentos: {', '.join(guide.documents)}")
    parts.append(f"fonte: {guide.source} (atualizado em {guide.updated_at.strftime('%d/%m/%Y')})")
    return "; ".join(parts)


def build_system_prompt(region: Region, context: RetrievedContext) -> str:
    persona = REGIONAL_AGENTS[region]
    records = [_render_unit(unit) for unit in context.units]
    records.extend(_render_guide(guide) for guide in context.guides)
    records_block = "\n".join(records) if records else "(nenhum registro encontrado)"

    return (
        f"Você é {persona.name}, assistente de saúde pública do Solano, com tom "
        f"{persona.tone}.\n{_SCOPE_RULES}\n\nRegistros disponíveis:\n{records_block}"
    )
