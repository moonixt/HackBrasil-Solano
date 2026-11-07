"""Base declarativa compartilhada pelos modelos em app.db.models.

Existe como módulo próprio para o Alembic enxergar o metadata sem
importar os modelos (e os módulos de domínio que eles trazem) direto.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
