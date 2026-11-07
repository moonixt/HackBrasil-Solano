"""Modelos de domínio: usuários, unidades de saúde, guias de serviço e sugestões.

Sem tabela de histórico de mensagens — o escopo do Solano proíbe guardar conteúdo
clínico ou conversa (ver README). A memória é só o que cada usuário informou no
onboarding (cidade, bairro) e os dados públicos de unidades/guias.
"""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import pg_enum
from app.domain.enums import OnboardingStep, Service, SuggestionStatus
from app.domain.regions import Region


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    uf: Mapped[str | None] = mapped_column(String(2))
    region: Mapped[Region | None] = mapped_column(pg_enum(Region, "region"))
    neighborhood: Mapped[str | None] = mapped_column(Text)
    onboarding_step: Mapped[OnboardingStep] = mapped_column(
        pg_enum(OnboardingStep, "onboarding_step"),
        nullable=False,
        default=OnboardingStep.AWAITING_CONTACT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class HealthUnit(Base):
    __tablename__ = "health_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    city_normalized: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    services: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    opening_hours: Mapped[str | None] = mapped_column(Text)
    accessibility: Mapped[str | None] = mapped_column(Text)
    scheduling: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[date] = mapped_column(Date, nullable=False)

    def offers(self, service: Service) -> bool:
        return service.value in self.services


class ServiceGuide(Base):
    __tablename__ = "service_guides"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    city_normalized: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    service: Mapped[Service] = mapped_column(pg_enum(Service, "service"), nullable=False)
    how_to: Mapped[str] = mapped_column(Text, nullable=False)
    documents: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[date] = mapped_column(Date, nullable=False)


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("health_units.id"))
    city: Mapped[str] = mapped_column(Text, nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SuggestionStatus] = mapped_column(
        pg_enum(SuggestionStatus, "suggestion_status"),
        nullable=False,
        default=SuggestionStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()
    unit: Mapped[HealthUnit | None] = relationship()
