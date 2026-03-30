from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import store

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/results")
async def get_result(alertname: str, namespace: str, pod: str):
    key = store.dedup_key(alertname, namespace, pod)
    record = store.get_incident(key)

    if record is None:
        raise HTTPException(status_code=404, detail="No result found for given params")

    if record.status == "pending":
        return JSONResponse(
            status_code=425,
            content={"detail": "agent still processing", "status": "pending", "dedup_key": key}
        )

    return record


@router.get("/incidents")
async def list_incidents():
    records = store.list_incidents()
    return {
        "total": len(records),
        "incidents": [
            {
                "dedup_key": r.dedup_key,
                "alertname": r.alertname,
                "namespace": r.namespace,
                "pod": r.pod,
                "status": r.status,
                "received_at": r.received_at,
                "completed_at": r.completed_at
            }
            for r in records
        ]
    }