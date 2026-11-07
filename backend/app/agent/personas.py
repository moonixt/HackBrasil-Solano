"""Camada leve de persona por região. Mesmo escopo e regras para todas — só tom e nome mudam."""

from dataclasses import dataclass

from app.domain.regions import Region


@dataclass(frozen=True)
class RegionalAgent:
    name: str
    tone: str


REGIONAL_AGENTS: dict[Region, RegionalAgent] = {
    Region.SUL: RegionalAgent(name="agente do Sul", tone="direto e objetivo"),
    Region.SUDESTE: RegionalAgent(name="agente do Sudeste", tone="prático e ágil"),
    Region.CENTRO_OESTE: RegionalAgent(name="agente do Centro-Oeste", tone="calmo e didático"),
    Region.NORTE: RegionalAgent(name="agente do Norte", tone="paciente e próximo"),
    Region.NORDESTE: RegionalAgent(name="agente do Nordeste", tone="acolhedor e caloroso"),
}
