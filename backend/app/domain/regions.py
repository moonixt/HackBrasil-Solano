"""Regiões do Brasil e o mapeamento oficial de UF para região (fonte: divisão do IBGE)."""

from enum import StrEnum


class Region(StrEnum):
    SUL = "sul"
    SUDESTE = "sudeste"
    CENTRO_OESTE = "centro_oeste"
    NORTE = "norte"
    NORDESTE = "nordeste"


UF_TO_REGION: dict[str, Region] = {
    # Sul
    "PR": Region.SUL,
    "RS": Region.SUL,
    "SC": Region.SUL,
    # Sudeste
    "ES": Region.SUDESTE,
    "MG": Region.SUDESTE,
    "RJ": Region.SUDESTE,
    "SP": Region.SUDESTE,
    # Centro-Oeste
    "DF": Region.CENTRO_OESTE,
    "GO": Region.CENTRO_OESTE,
    "MS": Region.CENTRO_OESTE,
    "MT": Region.CENTRO_OESTE,
    # Norte
    "AC": Region.NORTE,
    "AM": Region.NORTE,
    "AP": Region.NORTE,
    "PA": Region.NORTE,
    "RO": Region.NORTE,
    "RR": Region.NORTE,
    "TO": Region.NORTE,
    # Nordeste
    "AL": Region.NORDESTE,
    "BA": Region.NORDESTE,
    "CE": Region.NORDESTE,
    "MA": Region.NORDESTE,
    "PB": Region.NORDESTE,
    "PE": Region.NORDESTE,
    "PI": Region.NORDESTE,
    "RN": Region.NORDESTE,
    "SE": Region.NORDESTE,
}
