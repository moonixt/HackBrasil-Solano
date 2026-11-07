from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db.session import database_is_connected

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["connected", "disconnected"]


@router.get(
    "/health",
    response_model=HealthStatus,
    responses={503: {"model": HealthStatus}},
)
async def health() -> HealthStatus | JSONResponse:
    if await database_is_connected():
        return HealthStatus(status="ok", database="connected")

    return JSONResponse(
        status_code=503,
        content=HealthStatus(status="degraded", database="disconnected").model_dump(),
    )
