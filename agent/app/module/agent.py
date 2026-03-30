import logging
from datetime import datetime, timezone
from models import IncidentRecord, Alert
from claude_client import run_triage
import store

logger = logging.getLogger(__name__)


async def run_agent(record: IncidentRecord, alert: Alert):
    logger.info(f"Agent starting for {record.dedup_key}")
    try:
        report = run_triage(
            alertname=alert.labels.alertname,
            namespace=alert.labels.namespace,
            pod=alert.labels.pod,
            description=alert.annotations.description
        )
        record.report = report
        record.status = "completed"
        record.completed_at = datetime.now(timezone.utc)
        logger.info(f"Agent completed for {record.dedup_key}: {report.category}")
    except Exception as e:
        record.status = "failed"
        record.error = str(e)
        record.completed_at = datetime.now(timezone.utc)
        logger.error(f"Agent failed for {record.dedup_key}: {e}")
    finally:
        store.save_incident(record)