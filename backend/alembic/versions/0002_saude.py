"""usuários, unidades de saúde, guias de serviço e sugestões

Revision ID: 0002_saude
Revises: 0001_vector
Create Date: 2026-11-07

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_saude"
down_revision = "0001_vector"
branch_labels = None
depends_on = None

_REGION_VALUES = ("sul", "sudeste", "centro_oeste", "norte", "nordeste")
_SERVICE_VALUES = ("vacinacao", "consulta")
_SUGGESTION_STATUS_VALUES = ("pending", "verified", "rejected")

region_enum = postgresql.ENUM(*_REGION_VALUES, name="region")
service_enum = postgresql.ENUM(*_SERVICE_VALUES, name="service")
suggestion_status_enum = postgresql.ENUM(*_SUGGESTION_STATUS_VALUES, name="suggestion_status")


def upgrade() -> None:
    # Os tipos ENUM nativos são criados automaticamente pelo dialect do Postgres
    # na primeira CREATE TABLE que os referencia (create_type=True é o padrão).
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text()),
        sa.Column("phone", sa.Text()),
        sa.Column("city", sa.Text()),
        sa.Column("uf", sa.String(length=2)),
        sa.Column("region", region_enum),
        sa.Column("neighborhood", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("telegram_chat_id", name="uq_users_telegram_chat_id"),
    )
    op.create_index("ix_users_telegram_chat_id", "users", ["telegram_chat_id"])

    op.create_table(
        "health_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("city_normalized", sa.Text(), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("neighborhood", sa.Text()),
        sa.Column("address", sa.Text()),
        sa.Column("services", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("opening_hours", sa.Text()),
        sa.Column("accessibility", sa.Text()),
        sa.Column("scheduling", sa.Text()),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("updated_at", sa.Date(), nullable=False),
        sa.UniqueConstraint("external_key", name="uq_health_units_external_key"),
    )
    op.create_index("ix_health_units_city_normalized", "health_units", ["city_normalized"])

    op.create_table(
        "service_guides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_key", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("city_normalized", sa.Text(), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("service", service_enum, nullable=False),
        sa.Column("how_to", sa.Text(), nullable=False),
        sa.Column("documents", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("updated_at", sa.Date(), nullable=False),
        sa.UniqueConstraint("external_key", name="uq_service_guides_external_key"),
    )
    op.create_index("ix_service_guides_city_normalized", "service_guides", ["city_normalized"])

    op.create_table(
        "suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("unit_id", sa.Integer(), sa.ForeignKey("health_units.id")),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "status",
            suggestion_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_suggestions_status", "suggestions", ["status"])


def downgrade() -> None:
    op.drop_table("suggestions")
    op.drop_table("service_guides")
    op.drop_table("health_units")
    op.drop_table("users")

    bind = op.get_bind()
    suggestion_status_enum.drop(bind, checkfirst=True)
    service_enum.drop(bind, checkfirst=True)
    region_enum.drop(bind, checkfirst=True)
