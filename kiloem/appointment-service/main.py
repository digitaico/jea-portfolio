from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import asyncio
import nats
import os
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database import get_db, init_db, Appointment as DBAppointment

app = FastAPI(title="Appointment Service", version="1.0.0")

# NATS client
nats_client = None
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Data Models
class Appointment(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    duration_minutes: int = 30
    status: str = "scheduled"  # scheduled, confirmed, cancelled, completed
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AppointmentCreate(BaseModel):
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    duration_minutes: Optional[int] = 30
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# Event Schemas for NATS
class AppointmentEvent(BaseModel):
    event_type: str  # "appointment.scheduled", "appointment.updated", "appointment.cancelled"
    appointment_id: str
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    duration_minutes: int
    status: str
    notes: Optional[str] = None
    timestamp: datetime
    correlation_id: str


# NATS functions
async def init_nats():
    """Initialize NATS connection"""
    global nats_client
    try:
        nats_client = await nats.connect(NATS_URL)
        print(f"Connected to NATS at {NATS_URL}")
    except Exception as e:
        print(f"Failed to connect to NATS: {e}")

async def publish_event(event: AppointmentEvent):
    """Publish event to NATS"""
    if nats_client:
        try:
            event_data = event.model_dump_json()
            await nats_client.publish(event.event_type, event_data.encode())
            print(f"Published event: {event.event_type}")
        except Exception as e:
            print(f"Failed to publish event: {e}")

async def create_appointment_event(appointment: Appointment, event_type: str) -> AppointmentEvent:
    """Create an appointment event"""
    return AppointmentEvent(
        event_type=event_type,
        appointment_id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_time=appointment.appointment_time,
        duration_minutes=appointment.duration_minutes,
        status=appointment.status,
        notes=appointment.notes,
        timestamp=datetime.utcnow(),
        correlation_id=str(uuid.uuid4())
    )


@app.get("/")
async def root():
    return {"message": "Appointment Service API", "version": "1.0.0"}

@app.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new appointment"""
    appointment_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Create database appointment
    db_appointment = DBAppointment(
        id=appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_time=appointment.appointment_time,
        duration_minutes=appointment.duration_minutes or 30,
        notes=appointment.notes,
        created_at=now,
        updated_at=now
    )

    db.add(db_appointment)
    await db.commit()
    await db.refresh(db_appointment)

    # Convert to Pydantic model for response
    new_appointment = Appointment(
        id=db_appointment.id,
        patient_id=db_appointment.patient_id,
        doctor_id=db_appointment.doctor_id,
        appointment_time=db_appointment.appointment_time,
        duration_minutes=db_appointment.duration_minutes,
        status=db_appointment.status,
        notes=db_appointment.notes,
        created_at=db_appointment.created_at,
        updated_at=db_appointment.updated_at
    )

    # Publish event to NATS (Phase 2)
    if nats_client:
        event = await create_appointment_event(new_appointment, "appointment.scheduled")
        await publish_event(event)

    return new_appointment

@app.get("/appointments", response_model=List[Appointment])
async def list_appointments(db: AsyncSession = Depends(get_db)):
    """List all appointments"""
    result = await db.execute(select(DBAppointment))
    db_appointments = result.scalars().all()

    return [
        Appointment(
            id=apt.id,
            patient_id=apt.patient_id,
            doctor_id=apt.doctor_id,
            appointment_time=apt.appointment_time,
            duration_minutes=apt.duration_minutes,
            status=apt.status,
            notes=apt.notes,
            created_at=apt.created_at,
            updated_at=apt.updated_at
        )
        for apt in db_appointments
    ]

@app.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific appointment"""
    result = await db.execute(select(DBAppointment).where(DBAppointment.id == appointment_id))
    db_appointment = result.scalar_one_or_none()

    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return Appointment(
        id=db_appointment.id,
        patient_id=db_appointment.patient_id,
        doctor_id=db_appointment.doctor_id,
        appointment_time=db_appointment.appointment_time,
        duration_minutes=db_appointment.duration_minutes,
        status=db_appointment.status,
        notes=db_appointment.notes,
        created_at=db_appointment.created_at,
        updated_at=db_appointment.updated_at
    )

@app.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, update: AppointmentUpdate, db: AsyncSession = Depends(get_db)):
    """Update an appointment"""
    result = await db.execute(select(DBAppointment).where(DBAppointment.id == appointment_id))
    db_appointment = result.scalar_one_or_none()

    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Update fields if provided
    if update.appointment_time is not None:
        db_appointment.appointment_time = update.appointment_time
    if update.duration_minutes is not None:
        db_appointment.duration_minutes = update.duration_minutes
    if update.status is not None:
        db_appointment.status = update.status
    if update.notes is not None:
        db_appointment.notes = update.notes

    db_appointment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_appointment)

    # Convert to Pydantic model
    appointment = Appointment(
        id=db_appointment.id,
        patient_id=db_appointment.patient_id,
        doctor_id=db_appointment.doctor_id,
        appointment_time=db_appointment.appointment_time,
        duration_minutes=db_appointment.duration_minutes,
        status=db_appointment.status,
        notes=db_appointment.notes,
        created_at=db_appointment.created_at,
        updated_at=db_appointment.updated_at
    )

    # Publish event to NATS (Phase 2)
    if nats_client:
        event = await create_appointment_event(appointment, "appointment.updated")
        await publish_event(event)

    return appointment

@app.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel an appointment (soft delete by setting status)"""
    result = await db.execute(select(DBAppointment).where(DBAppointment.id == appointment_id))
    db_appointment = result.scalar_one_or_none()

    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db_appointment.status = "cancelled"
    db_appointment.updated_at = datetime.utcnow()
    await db.commit()

    # Convert to Pydantic model for event
    appointment = Appointment(
        id=db_appointment.id,
        patient_id=db_appointment.patient_id,
        doctor_id=db_appointment.doctor_id,
        appointment_time=db_appointment.appointment_time,
        duration_minutes=db_appointment.duration_minutes,
        status=db_appointment.status,
        notes=db_appointment.notes,
        created_at=db_appointment.created_at,
        updated_at=db_appointment.updated_at
    )

    # Publish event to NATS (Phase 2)
    if nats_client:
        event = await create_appointment_event(appointment, "appointment.cancelled")
        await publish_event(event)

    return {"message": "Appointment cancelled", "id": appointment_id}

@app.get("/appointments/patient/{patient_id}", response_model=List[Appointment])
async def get_patient_appointments(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get all appointments for a patient"""
    result = await db.execute(select(DBAppointment).where(DBAppointment.patient_id == patient_id))
    db_appointments = result.scalars().all()

    return [
        Appointment(
            id=apt.id,
            patient_id=apt.patient_id,
            doctor_id=apt.doctor_id,
            appointment_time=apt.appointment_time,
            duration_minutes=apt.duration_minutes,
            status=apt.status,
            notes=apt.notes,
            created_at=apt.created_at,
            updated_at=apt.updated_at
        )
        for apt in db_appointments
    ]

@app.get("/appointments/doctor/{doctor_id}", response_model=List[Appointment])
async def get_doctor_appointments(doctor_id: str, db: AsyncSession = Depends(get_db)):
    """Get all appointments for a doctor"""
    result = await db.execute(select(DBAppointment).where(DBAppointment.doctor_id == doctor_id))
    db_appointments = result.scalars().all()

    return [
        Appointment(
            id=apt.id,
            patient_id=apt.patient_id,
            doctor_id=apt.doctor_id,
            appointment_time=apt.appointment_time,
            duration_minutes=apt.duration_minutes,
            status=apt.status,
            notes=apt.notes,
            created_at=apt.created_at,
            updated_at=apt.updated_at
        )
        for apt in db_appointments
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
    uvicorn.run(app, host="0.0.0.0", port=8010)