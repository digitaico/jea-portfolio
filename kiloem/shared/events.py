"""
Shared Events Module
Defines common event schemas and types used across all services.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# Base Event Classes
class BaseEvent(BaseModel):
    """Base class for all events"""
    event_type: str
    correlation_id: str = None
    timestamp: datetime = None
    source_service: str = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

# Appointment Events
class AppointmentEvent(BaseEvent):
    """Base appointment event"""
    appointment_id: str
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    duration_minutes: int
    status: str
    notes: Optional[str] = None

class AppointmentScheduledEvent(AppointmentEvent):
    """Appointment scheduled event"""
    event_type: str = "appointment.scheduled"

class AppointmentUpdatedEvent(AppointmentEvent):
    """Appointment updated event"""
    event_type: str = "appointment.updated"

class AppointmentCancelledEvent(AppointmentEvent):
    """Appointment cancelled event"""
    event_type: str = "appointment.cancelled"

# Patient Events
class PatientEvent(BaseEvent):
    """Base patient event"""
    patient_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class PatientCreatedEvent(PatientEvent):
    """Patient created event"""
    event_type: str = "patient.created"

class PatientUpdatedEvent(PatientEvent):
    """Patient updated event"""
    event_type: str = "patient.updated"

# Notification Events
class NotificationEvent(BaseEvent):
    """Base notification event"""
    notification_id: str
    appointment_id: str
    patient_id: str
    notification_type: str  # "scheduled", "updated", "cancelled"
    message: str
    status: str = "sent"

class NotificationSentEvent(NotificationEvent):
    """Notification sent event"""
    event_type: str = "notification.sent"

# Doctor Events
class DoctorEvent(BaseEvent):
    """Base doctor event"""
    doctor_id: str
    name: str
    specialty: Optional[str] = None

class DoctorAvailabilityEvent(DoctorEvent):
    """Doctor availability event"""
    event_type: str = "doctor.availability.updated"
    available_slots: list

# Event Store Events
class EventStoreEvent(BaseEvent):
    """Event store event for persistence"""
    subject: str
    event_data: Dict[str, Any]
    stored_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.stored_at is None:
            self.stored_at = datetime.utcnow()

# Utility functions for event creation
def create_appointment_event(event_type: str, appointment_data: dict) -> AppointmentEvent:
    """Create appointment event from data"""
    event_classes = {
        "appointment.scheduled": AppointmentScheduledEvent,
        "appointment.updated": AppointmentUpdatedEvent,
        "appointment.cancelled": AppointmentCancelledEvent,
    }

    event_class = event_classes.get(event_type, AppointmentEvent)
    return event_class(event_type=event_type, **appointment_data)

def create_patient_event(event_type: str, patient_data: dict) -> PatientEvent:
    """Create patient event from data"""
    event_classes = {
        "patient.created": PatientCreatedEvent,
        "patient.updated": PatientUpdatedEvent,
    }

    event_class = event_classes.get(event_type, PatientEvent)
    return event_class(event_type=event_type, **patient_data)

def create_notification_event(event_type: str, notification_data: dict) -> NotificationEvent:
    """Create notification event from data"""
    event_classes = {
        "notification.sent": NotificationSentEvent,
    }

    event_class = event_classes.get(event_type, NotificationEvent)
    return event_class(event_type=event_type, **notification_data)

# Event subject patterns
class EventSubjects:
    """Standard event subject patterns"""
    APPOINTMENT_SCHEDULED = "appointment.scheduled"
    APPOINTMENT_UPDATED = "appointment.updated"
    APPOINTMENT_CANCELLED = "appointment.cancelled"

    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"

    NOTIFICATION_SENT = "notification.sent"

    DOCTOR_AVAILABILITY = "doctor.availability.updated"

    # Wildcard patterns for subscriptions
    ALL_APPOINTMENTS = "appointment.*"
    ALL_PATIENTS = "patient.*"
    ALL_NOTIFICATIONS = "notification.*"
    ALL_DOCTORS = "doctor.*"
    ALL_EVENTS = ">"

# Event validation utilities
def validate_event_data(event: BaseEvent) -> bool:
    """Validate event data structure"""
    try:
        # Check required fields based on event type
        if hasattr(event, 'appointment_id') and not event.appointment_id:
            return False
        if hasattr(event, 'patient_id') and not event.patient_id:
            return False
        if hasattr(event, 'correlation_id') and not event.correlation_id:
            return False
        return True
    except Exception:
        return False

def get_event_summary(event: BaseEvent) -> str:
    """Get human-readable event summary"""
    if hasattr(event, 'appointment_id'):
        return f"{event.event_type} for appointment {event.appointment_id}"
    elif hasattr(event, 'patient_id'):
        return f"{event.event_type} for patient {event.patient_id}"
    elif hasattr(event, 'notification_id'):
        return f"{event.event_type} for notification {event.notification_id}"
    else:
        return f"{event.event_type}"