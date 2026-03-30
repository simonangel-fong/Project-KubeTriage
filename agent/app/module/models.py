from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertLabels(BaseModel):
    alertname: str
    namespace: str
    pod: str
    container: str
    reason: Optional[str] = None
    severity: Optional[str] = None
    team: Optional[str] = None
    uid: Optional[str] = None
    instance: Optional[str] = None
    job: Optional[str] = None
    service: Optional[str] = None
    prometheus: Optional[str] = None
    endpoint: Optional[str] = None


class AlertAnnotations(BaseModel):
    summary: str
    description: str


class Alert(BaseModel):
    status: str
    labels: AlertLabels
    annotations: AlertAnnotations
    startsAt: datetime
    endsAt: datetime
    generatorURL: str
    fingerprint: str


class AlertmanagerPayload(BaseModel):
    receiver: str
    status: str
    alerts: list[Alert]
    groupLabels: dict
    commonLabels: dict
    commonAnnotations: dict
    externalURL: str
    version: str
    groupKey: str
    truncatedAlerts: int


class TriageReport(BaseModel):
    category: str
    root_cause: str
    remediation: list[str]
    kubectl_command: str
    escalate: bool


class IncidentRecord(BaseModel):
    dedup_key: str
    alertname: str
    namespace: str
    pod: str
    container: str
    reason: Optional[str] = None
    status: str                          # pending | completed | failed
    received_at: datetime
    completed_at: Optional[datetime] = None
    alert: Optional[Alert] = None
    report: Optional[TriageReport] = None
    error: Optional[str] = None