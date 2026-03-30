import time
from models import IncidentRecord

# keyed by dedup_key
incidents: dict[str, IncidentRecord] = {}

# keyed by dedup_key, value is expiry unix timestamp
dedup_cache: dict[str, float] = {}

DEDUP_TTL_SECONDS = 600  # 10 minutes


def dedup_key(alertname: str, namespace: str, pod: str) -> str:
    return f"{alertname}:{namespace}:{pod}"


def is_duplicate(key: str) -> bool:
    expiry = dedup_cache.get(key)
    if expiry is None:
        return False
    if time.time() > expiry:
        del dedup_cache[key]
        return False
    return True


def register(key: str):
    dedup_cache[key] = time.time() + DEDUP_TTL_SECONDS


def get_incident(key: str) -> IncidentRecord | None:
    return incidents.get(key)


def save_incident(record: IncidentRecord):
    incidents[key] = record


def save_incident(record: IncidentRecord):
    incidents[record.dedup_key] = record


def list_incidents() -> list[IncidentRecord]:
    return list(incidents.values())