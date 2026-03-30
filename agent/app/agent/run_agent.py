import logging
from datetime import datetime, timezone
from ..models import AlertInfo
from .kubetriage_agent import run_triage

logger = logging.getLogger(__name__)


async def run_agent(alertInfo: AlertInfo):
    # logger.info(f"Agent starting for {record.dedup_key}")
    logger.info(f"========== run_agent ==========")
    try:
        report = run_triage(
            alertname=alertInfo.alertname,
            namespace=alertInfo.namespace,
            pod=alertInfo.pod,
            description=alertInfo.description
        )
        logger.info(f"report: {report}")
        logger.info(f"Agent completed")
    except Exception as e:
        logger.error(f"Agent failed: {e}")
