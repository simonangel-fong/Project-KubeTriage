import logging
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException
from models import AlertmanagerPayload, IncidentRecord
import store
from agent import run_agent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook/alertmanager", status_code=202)
async def receive_alert(
    payload: AlertmanagerPayload,
    background_tasks: BackgroundTasks
):
    results = []

    for alert in payload.alerts:
        if alert.status != "firing":
            continue

        key = store.dedup_key(
            alert.labels.alertname,
            alert.labels.namespace,
            alert.labels.pod
        )

        if store.is_duplicate(key):
            logger.info(f"Deduplicated: {key}")
            results.append({"dedup_key": key, "status": "deduplicated"})
            continue

        store.register(key)

        record = IncidentRecord(
            dedup_key=key,
            alertname=alert.labels.alertname,
            namespace=alert.labels.namespace,
            pod=alert.labels.pod,
            container=alert.labels.container,
            reason=alert.labels.reason,
            status="pending",
            received_at=datetime.now(timezone.utc),
            alert=alert
        )
        store.save_incident(record)
        background_tasks.add_task(run_agent, record, alert)

        logger.info(f"Accepted: {key}")
        results.append({"dedup_key": key, "status": "accepted"})

    return {"results": results}
