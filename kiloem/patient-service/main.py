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
from sqlalchemy import select

from database import get_db, init_db, Patient as DBPatient

app = FastAPI(title="Patient Contact Service", version="1.0.0")

# NATS client
nats_client = None
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Pydantic Models
class Patient(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class PatientCreate(BaseModel):
    name: str
    email: str
    phone: str
    notification_preferences: Optional[dict] = {"email": True, "sms": False}

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notification_preferences: Optional[dict] = None

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

class PatientEvent(BaseModel):
    event_type: str  # "patient.created", "patient.updated"
    patient_id: str
    name: str
    email: str
    phone: str
    notification_preferences: dict
    timestamp: datetime
    correlation_id: str


# NATS functions
async def init_nats():
    """Initialize NATS connection"""
    global nats_client
    try:
        nats_client = await nats.connect(NATS_URL)
        print(f"Connected to NATS at {NATS_URL}")

        # Subscribe to appointment events to track patient activity
        await nats_client.subscribe("appointment.*", cb=appointment_event_handler)

        print("Subscribed to appointment.* events")
    except Exception as e:
        print(f"Failed to connect to NATS: {e}")

async def appointment_event_handler(msg):
    """Handle incoming appointment events to track patient activity"""
    try:
        event_data = json.loads(msg.data.decode())
        event = AppointmentEvent(**event_data)

        print(f"Received appointment event: {event.event_type} for patient {event.patient_id}")

        # Get database session and ensure patient exists
        async for db in get_db():
            result = await db.execute(select(DBPatient).where(DBPatient.id == event.patient_id))
            db_patient = result.scalar_one_or_none()

            if not db_patient:
                # Create a placeholder patient record if we don't have one
                db_patient = DBPatient(
                    id=event.patient_id,
                    name=f"Patient {event.patient_id}",
                    email=f"patient.{event.patient_id}@example.com",
                    phone="+1234567890",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(db_patient)
                await db.commit()
                await db.refresh(db_patient)
                print(f"Created placeholder patient record for {event.patient_id}")
            break

    except Exception as e:
        print(f"Error processing appointment event: {e}")

async def publish_patient_event(db_patient: DBPatient, event_type: str):
    """Publish patient event to NATS"""
    if nats_client:
        try:
            event = PatientEvent(
                event_type=event_type,
                patient_id=db_patient.id,
                name=db_patient.name,
                email=db_patient.email,
                phone=db_patient.phone,
                notification_preferences={"email": True, "sms": False},  # Default for now
                timestamp=datetime.utcnow(),
                correlation_id=str(uuid.uuid4())
            )

            event_data = event.model_dump_json()
            await nats_client.publish(f"patient.{event_type.split('.')[-1]}", event_data.encode())
            print(f"Published patient event: {event_type}")

        except Exception as e:
            print(f"Error publishing patient event: {e}")

@app.get("/")
async def root():
    return {"message": "Patient Contact Service API", "version": "1.0.0"}

@app.post("/patients", response_model=Patient)
async def create_patient(patient: PatientCreate):
    """Create a new patient"""
    patient_id = str(uuid.uuid4())
    now = datetime.utcnow()

    new_patient = Patient(
        id=patient_id,
        name=patient.name,
        email=patient.email,
        phone=patient.phone,
        notification_preferences=patient.notification_preferences or {"email": True, "sms": False},
        created_at=now,
        updated_at=now
    )

    patients_db[patient_id] = new_patient

    # Publish event to NATS (Phase 4)
    await publish_patient_event(new_patient, "patient.created")

    return new_patient

@app.get("/patients", response_model=List[Patient])
async def list_patients():
    """List all patients"""
    return list(patients_db.values())

@app.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    """Get a specific patient"""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patients_db[patient_id]

@app.put("/patients/{patient_id}", response_model=Patient)
async def update_patient(patient_id: str, update: PatientUpdate):
    """Update a patient"""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = patients_db[patient_id]

    # Update fields if provided
    if update.name is not None:
        patient.name = update.name
    if update.email is not None:
        patient.email = update.email
    if update.phone is not None:
        patient.phone = update.phone
    if update.notification_preferences is not None:
        patient.notification_preferences = update.notification_preferences

    patient.updated_at = datetime.utcnow()

    # Publish event to NATS (Phase 4)
    await publish_patient_event(patient, "patient.updated")

    return patient

@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient"""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    del patients_db[patient_id]
    return {"message": "Patient deleted", "id": patient_id}

@app.get("/patients/search/email/{email}")
async def find_patient_by_email(email: str):
    """Find patient by email"""
    for patient in patients_db.values():
        if patient.email == email:
            return patient
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/patients/search/phone/{phone}")
async def find_patient_by_phone(phone: str):
    """Find patient by phone"""
    for patient in patients_db.values():
        if patient.phone == phone:
            return patient
    raise HTTPException(status_code=404, detail="Patient not found")

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
    uvicorn.run(app, host="0.0.0.0", port=8012)