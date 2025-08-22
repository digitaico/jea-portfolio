from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None
    version: str = "1.0"

class OrderCreatedEvent(BaseEvent):
    event_type: str = "order.created"
    data: dict

class OrderProcessedEvent(BaseEvent):
    event_type: str = "order.processed"
    data: dict

class NotificationSentEvent(BaseEvent):
    event_type: str = "notification.sent"
    data: dict