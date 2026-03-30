# routers/webhook.py
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks
from ..models import AlertmanagerPayload

from ..config import get_settings
from ..models import AlertInfo
from ..agent import run_triage

router = APIRouter(prefix="/webhook", tags=["health"])

logger = logging.getLogger(__name__)

settings = get_settings()


@router.post("/alertmanager", status_code=202)
async def get_alert(
    payload: AlertmanagerPayload,
    background_tasks: BackgroundTasks
):
    for alert in payload.alerts:

        if alert.status != "firing":
            continue

        alertInfo = AlertInfo(
            alertname=alert.labels.alertname,
            namespace=alert.labels.namespace,
            pod=alert.labels.pod,
            container=alert.labels.container,
            reason=alert.labels.reason,
            received_at=datetime.now(timezone.utc),
            description=alert.annotations.description
        )
        background_tasks.add_task(run_triage, alertInfo)
