from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional


class LogEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service: str
    level: str
    message: str
    metadata: Optional[dict] = None


class MetricEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service: str
    metric_name: str
    value: float
    tags: Optional[dict] = None