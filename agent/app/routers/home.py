# router/home.py
import os
from fastapi import APIRouter

from config.setting import get_settings

# ====================
# Root endpoint
# ====================

router = APIRouter(prefix="", tags=["home"])
settings = get_settings()

HOSTNAME = os.getenv("HOSTNAME", "my_host")


@router.get(
    "/",
    tags=["root"],
    summary="Service status",
    description=(
        "Return basic information about the Device Management API service. "
    ),
)
async def home() -> dict:
    """
    Return basic service metadata and status.
    """
    response: dict = {
        "project": settings.project,
        "status": "ok",
        "environment": settings.env,
        "debug": settings.debug,
        "docs": {
            "openapi": "/openapi.json",
            "swagger_ui": "/docs",
            "redoc": "/redoc",
        },
    }

    if settings.debug:
        response["fastapi"] = {
            "fastapi_host": HOSTNAME,
        }

    return response
