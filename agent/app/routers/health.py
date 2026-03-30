# app/routers/health.py
import logging
from fastapi import APIRouter

from config import get_settings

router = APIRouter(prefix="/health", tags=["health"])

logger = logging.getLogger(__name__)

settings = get_settings()


@router.get("/", summary="App health check")
async def health() -> dict:
    """
    Basic app-level health check.
    """
    return {
        "status": "ok",
        "project": settings.project,
        "environment": settings.env,
    }

