from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.telegram import router as telegram_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(telegram_router)
api_router.include_router(admin_router)
