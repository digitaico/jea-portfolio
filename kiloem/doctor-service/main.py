from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import asyncio
import nats
import os
import json

app = FastAPI(title="Doctor Availability Service", version="1.0.0")

# NATS client
nats_client = None
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Data Models
class Doctor(BaseModel):
    id: str
    name: str
    specialty: str
    email: str
    phone: str
    created_at: datetime
    updated_at: datetime

class AvailabilitySlot(BaseModel):
    id: str
    doctor_id: str
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    appointment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DoctorCreate(BaseModel):
    name: str
    specialty: str
    email: str
    phone: str

class AvailabilityCreate(BaseModel):
    doctor_id: str
    start_time: datetime
    duration_hours: int = 1

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

class AvailabilityEvent(BaseModel):
    event_type: str  # "availability.updated", "availability.blocked", "availability.freed"
    availability_id: str
    doctor_id: str
    start_time: datetime
    end_time: datetime
    is_available: bool
    appointment_id: Optional[str] = None
    timestamp: datetime
    correlation_id: str

# In-memory storage (will be replaced with database in Phase 6)
doctors_db = {}
availability_db = {}

# NATS functions
async def init_nats():
    """Initialize NATS connection"""
    global nats_client
    try:
        nats_client = await nats.connect(NATS_URL)
        print(f"Connected to NATS at {NATS_URL}")

        # Subscribe to appointment events to manage availability
        await nats_client.subscribe("appointment.*", cb=appointment_event_handler)

        print("Subscribed to appointment.* events")
    except Exception as e:
        print(f"Failed to connect to NATS: {e}")

async def appointment_event_handler(msg):
    """Handle incoming appointment events to manage doctor availability"""
    try:
        event_data = json.loads(msg.data.decode())
        event = AppointmentEvent(**event_data)

        print(f"Received appointment event: {event.event_type} for doctor {event.doctor_id}")

        if event.event_type == "appointment.scheduled":
            await block_availability(event)
        elif event.event_type == "appointment.cancelled":
            await free_availability(event)
        elif event.event_type == "appointment.updated":
            # Handle rescheduling - free old slot and block new one
            await handle_reschedule(event)

    except Exception as e:
        print(f"Error processing appointment event: {e}")

async def block_availability(appointment_event: AppointmentEvent):
    """Block availability slot for scheduled appointment"""
    try:
        # Find overlapping availability slots
        overlapping_slots = [
            slot for slot in availability_db.values()
            if slot.doctor_id == appointment_event.doctor_id
            and slot.start_time <= appointment_event.appointment_time
            and slot.end_time >= (appointment_event.appointment_time + timedelta(minutes=appointment_event.duration_minutes))
            and slot.is_available
        ]

        for slot in overlapping_slots:
            slot.is_available = False
            slot.appointment_id = appointment_event.appointment_id
            slot.updated_at = datetime.utcnow()

            # Publish availability event
            await publish_availability_event(slot, "availability.blocked")

            print(f"Blocked availability slot {slot.id} for appointment {appointment_event.appointment_id}")

    except Exception as e:
        print(f"Error blocking availability: {e}")

async def free_availability(appointment_event: AppointmentEvent):
    """Free availability slot when appointment is cancelled"""
    try:
        # Find slots blocked by this appointment
        blocked_slots = [
            slot for slot in availability_db.values()
            if slot.doctor_id == appointment_event.doctor_id
            and slot.appointment_id == appointment_event.appointment_id
            and not slot.is_available
        ]

        for slot in blocked_slots:
            slot.is_available = True
            slot.appointment_id = None
            slot.updated_at = datetime.utcnow()

            # Publish availability event
            await publish_availability_event(slot, "availability.freed")

            print(f"Freed availability slot {slot.id} from cancelled appointment {appointment_event.appointment_id}")

    except Exception as e:
        print(f"Error freeing availability: {e}")

async def handle_reschedule(appointment_event: AppointmentEvent):
    """Handle appointment rescheduling"""
    try:
        # This is a simplified version - in production, you'd need the old appointment details
        # For now, we'll just ensure the slot is properly managed
        print(f"Handling reschedule for appointment {appointment_event.appointment_id}")

        # You could implement more complex logic here to handle time changes
        # For this demo, we'll just ensure availability is properly managed

    except Exception as e:
        print(f"Error handling reschedule: {e}")

async def publish_availability_event(slot: AvailabilitySlot, event_type: str):
    """Publish availability event to NATS"""
    if nats_client:
        try:
            event = AvailabilityEvent(
                event_type=event_type,
                availability_id=slot.id,
                doctor_id=slot.doctor_id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                is_available=slot.is_available,
                appointment_id=slot.appointment_id,
                timestamp=datetime.utcnow(),
                correlation_id=str(uuid.uuid4())
            )

            event_data = event.model_dump_json()
            await nats_client.publish(f"availability.{event_type.split('.')[-1]}", event_data.encode())
            print(f"Published availability event: {event_type}")

        except Exception as e:
            print(f"Error publishing availability event: {e}")

@app.get("/")
async def root():
    return {"message": "Doctor Availability Service API", "version": "1.0.0"}

@app.post("/doctors", response_model=Doctor)
async def create_doctor(doctor: DoctorCreate):
    """Create a new doctor"""
    doctor_id = str(uuid.uuid4())
    now = datetime.utcnow()

    new_doctor = Doctor(
        id=doctor_id,
        name=doctor.name,
        specialty=doctor.specialty,
        email=doctor.email,
        phone=doctor.phone,
        created_at=now,
        updated_at=now
    )

    doctors_db[doctor_id] = new_doctor
    return new_doctor

@app.get("/doctors", response_model=List[Doctor])
async def list_doctors():
    """List all doctors"""
    return list(doctors_db.values())

@app.get("/doctors/{doctor_id}", response_model=Doctor)
async def get_doctor(doctor_id: str):
    """Get a specific doctor"""
    if doctor_id not in doctors_db:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctors_db[doctor_id]

@app.post("/availability", response_model=AvailabilitySlot)
async def create_availability(availability: AvailabilityCreate):
    """Create availability slots for a doctor"""
    if availability.doctor_id not in doctors_db:
        raise HTTPException(status_code=404, detail="Doctor not found")

    slot_id = str(uuid.uuid4())
    now = datetime.utcnow()
    end_time = availability.start_time + timedelta(hours=availability.duration_hours)

    new_slot = AvailabilitySlot(
        id=slot_id,
        doctor_id=availability.doctor_id,
        start_time=availability.start_time,
        end_time=end_time,
        created_at=now,
        updated_at=now
    )

    availability_db[slot_id] = new_slot

    # Publish availability event
    await publish_availability_event(new_slot, "availability.updated")

    return new_slot

@app.get("/availability/doctor/{doctor_id}", response_model=List[AvailabilitySlot])
async def get_doctor_availability(doctor_id: str):
    """Get availability slots for a doctor"""
    if doctor_id not in doctors_db:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_slots = [
        slot for slot in availability_db.values()
        if slot.doctor_id == doctor_id
    ]
    return doctor_slots

@app.get("/availability/available/{doctor_id}", response_model=List[AvailabilitySlot])
async def get_available_slots(doctor_id: str):
    """Get available slots for a doctor"""
    if doctor_id not in doctors_db:
        raise HTTPException(status_code=404, detail="Doctor not found")

    available_slots = [
        slot for slot in availability_db.values()
        if slot.doctor_id == doctor_id and slot.is_available
    ]
    return available_slots

@app.get("/availability")
async def get_all_availability():
    """Get all availability slots"""
    return list(availability_db.values())

@app.on_event("startup")
async def startup_event():
    """Initialize NATS connection on startup"""
    await init_nats()

@app.on_event("shutdown")
async def shutdown_event():
    """Close NATS connection on shutdown"""
    if nats_client:
        await nats_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)