from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertInfo(BaseModel):
    alertname: str
    namespace: str
    pod: str
    container: str
    reason: Optional[str] = None
    received_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    description: str = ""
