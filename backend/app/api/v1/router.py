from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.matches import router as matches_router
from app.api.v1.teams import router as teams_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(matches_router)
api_v1_router.include_router(teams_router)
api_v1_router.include_router(chat_router)
