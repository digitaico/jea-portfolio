from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import asyncio
import nats
import os
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, init_db, Notification as DBNotification

app = FastAPI(title="Notifications Service", version="1.0.0")

# NATS client
nats_client = None
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Event Schemas
class AppointmentEvent(BaseModel):
    event_type: str
    appointment_id: str
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    duration_minutes: int
    status: str
    notes: Optional[str] = None
    timestamp: datetime
    correlation_id: str

class NotificationEvent(BaseModel):
    event_type: str  # "notification.sent"
    notification_id: str
    appointment_id: str
    patient_id: str
    notification_type: str  # "appointment_scheduled", "appointment_updated", "appointment_cancelled"
    message: str
    timestamp: datetime
    correlation_id: str


# NATS functions
async def init_nats():
    """Initialize NATS connection"""
    global nats_client
    try:
        nats_client = await nats.connect(NATS_URL)
        print(f"Connected to NATS at {NATS_URL}")

        # Subscribe to appointment events
        await nats_client.subscribe("appointment.*", cb=appointment_event_handler)

        print("Subscribed to appointment.* events")
    except Exception as e:
        print(f"Failed to connect to NATS: {e}")

async def appointment_event_handler(msg):
    """Handle incoming appointment events"""
    try:
        event_data = json.loads(msg.data.decode())
        event = AppointmentEvent(**event_data)

        print(f"Received event: {event.event_type} for appointment {event.appointment_id}")

        # Get database session
        async for db in get_db():
            # Process notification based on event type
            if event.event_type == "appointment.scheduled":
                await send_appointment_notification(event, "scheduled", db)
            elif event.event_type == "appointment.updated":
                await send_appointment_notification(event, "updated", db)
            elif event.event_type == "appointment.cancelled":
                await send_appointment_notification(event, "cancelled", db)
            break

    except Exception as e:
        print(f"Error processing appointment event: {e}")

async def send_appointment_notification(appointment_event: AppointmentEvent, notification_type: str, db: AsyncSession = None):
    """Send notification for appointment event"""
    try:
        # Create notification message
        if notification_type == "scheduled":
            message = f"Your appointment with Dr. {appointment_event.doctor_id} is scheduled for {appointment_event.appointment_time.strftime('%Y-%m-%d %H:%M')}."
        elif notification_type == "updated":
            message = f"Your appointment with Dr. {appointment_event.doctor_id} has been updated."
        elif notification_type == "cancelled":
            message = f"Your appointment with Dr. {appointment_event.doctor_id} has been cancelled."
        else:
            message = f"Appointment notification: {notification_type}"

        # Create database notification
        notification_id = str(uuid.uuid4())
        now = datetime.utcnow()

        db_notification = DBNotification(
            id=notification_id,
            patient_id=appointment_event.patient_id,
            appointment_id=appointment_event.appointment_id,
            type=notification_type,
            message=message,
            status="sent",
            sent_at=now,
            created_at=now
        )

        if db:
            db.add(db_notification)
            await db.commit()
            await db.refresh(db_notification)

        print(f"📧 Notification sent to patient {appointment_event.patient_id}: {message}")

        # Publish notification event to NATS
        if nats_client:
            notification_event = NotificationEvent(
                event_type="notification.sent",
                notification_id=notification_id,
                appointment_id=appointment_event.appointment_id,
                patient_id=appointment_event.patient_id,
                notification_type=notification_type,
                message=message,
                timestamp=now,
                correlation_id=str(uuid.uuid4())
            )

            event_data = notification_event.model_dump_json()
            await nats_client.publish("notification.sent", event_data.encode())
            print(f"Published notification event: notification.sent")

    except Exception as e:
        print(f"Error sending notification: {e}")

@app.get("/")
async def root():
    return {"message": "Notifications Service API", "version": "1.0.0"}

@app.get("/notifications")
async def get_notifications(db: AsyncSession = Depends(get_db)):
    """Get all notifications"""
    result = await db.execute(select(DBNotification))
    db_notifications = result.scalars().all()

    return [
        {
            "id": n.id,
            "patient_id": n.patient_id,
            "appointment_id": n.appointment_id,
            "type": n.type,
            "message": n.message,
            "status": n.status,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat()
        }
        for n in db_notifications
    ]

@app.get("/notifications/appointment/{appointment_id}")
async def get_appointment_notifications(appointment_id: str, db: AsyncSession = Depends(get_db)):
    """Get notifications for a specific appointment"""
    result = await db.execute(select(DBNotification).where(DBNotification.appointment_id == appointment_id))
    db_notifications = result.scalars().all()

    return [
        {
            "id": n.id,
            "patient_id": n.patient_id,
            "appointment_id": n.appointment_id,
            "type": n.type,
            "message": n.message,
            "status": n.status,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat()
        }
        for n in db_notifications
    ]

@app.get("/notifications/patient/{patient_id}")
async def get_patient_notifications(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get notifications for a specific patient"""
    result = await db.execute(select(DBNotification).where(DBNotification.patient_id == patient_id))
    db_notifications = result.scalars().all()

    return [
        {
            "id": n.id,
            "patient_id": n.patient_id,
            "appointment_id": n.appointment_id,
            "type": n.type,
            "message": n.message,
            "status": n.status,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat()
        }
        for n in db_notifications
    ]

@app.on_event("startup")
async def startup_event():
    """Initialize database and NATS connection on startup"""
    await init_db()
    await init_nats()

@app.on_event("shutdown")
async def shutdown_event():
    """Close NATS connection on shutdown"""
    if nats_client:
        await nats_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)