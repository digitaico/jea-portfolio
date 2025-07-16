from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel


class BaseEvent(BaseModel):
    """Base event model"""
    event_id: UUID
    event_type: str
    timestamp: datetime
    session_id: UUID
    data: Dict[str, Any]


class VideoUploadedEvent(BaseEvent):
    """Event fired when video is uploaded"""
    event_type: str = "video_uploaded"


class PoseDetectionCompletedEvent(BaseEvent):
    """Event fired when pose detection is completed"""
    event_type: str = "pose_detection_completed"


class MetricsCalculatedEvent(BaseEvent):
    """Event fired when metrics are calculated"""
    event_type: str = "metrics_calculated"


class ReportGeneratedEvent(BaseEvent):
    """Event fired when report is generated"""
    event_type: str = "report_generated"


class ProcessingFailedEvent(BaseEvent):
    """Event fired when processing fails"""
    event_type: str = "processing_failed"
    error_message: str