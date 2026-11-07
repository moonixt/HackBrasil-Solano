"""Revisão humana de sugestões. Verificar NÃO edita unidades automaticamente —
alguém edita o arquivo de dados e reexecuta o seed."""

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Suggestion
from app.db.session import get_session
from app.domain.enums import SuggestionStatus

router = APIRouter(prefix="/admin", tags=["admin"])

_TOKEN_HEADER = "X-Admin-Token"


class SuggestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    unit_id: int | None
    city: str
    uf: str
    text: str
    status: SuggestionStatus
    created_at: datetime
    reviewed_at: datetime | None


class ReviewBody(BaseModel):
    status: Literal[SuggestionStatus.VERIFIED, SuggestionStatus.REJECTED]


def _require_admin(request: Request) -> None:
    settings = get_settings()
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="painel de admin desligado")
    if request.headers.get(_TOKEN_HEADER) != settings.admin_token:
        raise HTTPException(status_code=403)


@router.get("/suggestions", response_model=list[SuggestionOut])
async def list_suggestions(
    request: Request,
    status: SuggestionStatus | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Suggestion]:
    _require_admin(request)

    query = select(Suggestion).order_by(Suggestion.created_at.desc())
    if status is not None:
        query = query.where(Suggestion.status == status)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post("/suggestions/{suggestion_id}/review", response_model=SuggestionOut)
async def review_suggestion(
    request: Request,
    suggestion_id: int,
    body: ReviewBody,
    session: AsyncSession = Depends(get_session),
) -> Suggestion:
    _require_admin(request)

    suggestion = await session.get(Suggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404)

    suggestion.status = body.status
    suggestion.reviewed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(suggestion)
    return suggestion
