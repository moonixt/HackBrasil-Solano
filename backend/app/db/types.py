"""Helper para colunas de enum nativo do Postgres a partir de um StrEnum."""

from enum import StrEnum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=StrEnum)


def pg_enum(enum_cls: type[E], name: str) -> SAEnum:
    return SAEnum(enum_cls, name=name, values_callable=lambda cls: [member.value for member in cls])
