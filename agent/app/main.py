# app/main.py
from __future__ import annotations

import logging
from fastapi import FastAPI

from routers import home, health

# from webhook import router as webhook_router
# from routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)

app = FastAPI(
    title="KubeTriage",
    version="0.1.0",
    description=("AN AI agent assistance for Kubernetes"),
)


app = FastAPI(title="KubeTriage", version="0.1.0")
app.include_router(home.router)
app.include_router(health.router)
# app.include_router(api_router)
