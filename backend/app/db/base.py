"""Base declarativa para os modelos futuros.

Tabelas de domínio (usuários, regiões, memória compartilhada) entram nas
issues seguintes. Esta base existe para o Alembic enxergar o metadata.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
