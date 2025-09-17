from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import nats
import os
import json

from shared.events import (
    AppointmentCreateCommand, AppointmentUpdateCommand, AppointmentCancelCommand,
    AppointmentGetCommand, AppointmentListCommand,
    AppointmentCreatedResponse, AppointmentUpdatedResponse, AppointmentCancelledResponse,
    AppointmentDataResponse, AppointmentListResponse,
    EventSubjects
)

app = FastAPI(title="API Gateway", version="1.0.0")

# NATS client
nats_client = None
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Pending requests: correlation_id -> Future
pending_requests = {}

# Data Models
class Appointment(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    duration_minutes: int
    status: str
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

# NATS functions
async def init_nats():
    global nats_client
    nats_client = await nats.connect(NATS_URL)
    print(f"Connected to NATS at {NATS_URL}")

    # Subscribe to response events
    await nats_client.subscribe(EventSubjects.APPOINTMENT_CREATED_RESPONSE, cb=handle_appointment_created)
    await nats_client.subscribe(EventSubjects.APPOINTMENT_UPDATED_RESPONSE, cb=handle_appointment_updated)
    await nats_client.subscribe(EventSubjects.APPOINTMENT_CANCELLED_RESPONSE, cb=handle_appointment_cancelled)
    await nats_client.subscribe(EventSubjects.APPOINTMENT_DATA_RESPONSE, cb=handle_appointment_data)
    await nats_client.subscribe(EventSubjects.APPOINTMENT_LIST_RESPONSE, cb=handle_appointment_list)

async def publish_command(command):
    if nats_client:
        event_data = command.model_dump_json()
        await nats_client.publish(command.event_type, event_data.encode())
        print(f"Published command: {command.event_type}")

# Response handlers
async def handle_appointment_created(msg):
    data = json.loads(msg.data.decode())
    response = AppointmentCreatedResponse(**data)
    future = pending_requests.pop(response.correlation_id, None)
    if future:
        appointment = Appointment(
            id=response.appointment_id,
            patient_id=response.patient_id,
            doctor_id=response.doctor_id,
            appointment_time=response.appointment_time,
            duration_minutes=response.duration_minutes,
            status=response.status,
            notes=response.notes,
            created_at=response.created_at,
            updated_at=response.updated_at
        )
        future.set_result(appointment)

async def handle_appointment_updated(msg):
    data = json.loads(msg.data.decode())
    response = AppointmentUpdatedResponse(**data)
    future = pending_requests.pop(response.correlation_id, None)
    if future:
        appointment = Appointment(
            id=response.appointment_id,
            patient_id=response.patient_id,
            doctor_id=response.doctor_id,
            appointment_time=response.appointment_time,
            duration_minutes=response.duration_minutes,
            status=response.status,
            notes=response.notes,
            created_at=response.created_at,
            updated_at=response.updated_at
        )
        future.set_result(appointment)

async def handle_appointment_cancelled(msg):
    data = json.loads(msg.data.decode())
    response = AppointmentCancelledResponse(**data)
    future = pending_requests.pop(response.correlation_id, None)
    if future:
        future.set_result({"message": "Appointment cancelled", "id": response.appointment_id})

async def handle_appointment_data(msg):
    data = json.loads(msg.data.decode())
    response = AppointmentDataResponse(**data)
    future = pending_requests.pop(response.correlation_id, None)
    if future:
        appointment = Appointment(
            id=response.appointment_id,
            patient_id=response.patient_id,
            doctor_id=response.doctor_id,
            appointment_time=response.appointment_time,
            duration_minutes=response.duration_minutes,
            status=response.status,
            notes=response.notes,
            created_at=response.created_at,
            updated_at=response.updated_at
        )
        future.set_result(appointment)

async def handle_appointment_list(msg):
    data = json.loads(msg.data.decode())
    response = AppointmentListResponse(**data)
    future = pending_requests.pop(response.correlation_id, None)
    if future:
        appointments = [
            Appointment(
                id=apt['id'],
                patient_id=apt['patient_id'],
                doctor_id=apt['doctor_id'],
                appointment_time=apt['appointment_time'],
                duration_minutes=apt['duration_minutes'],
                status=apt['status'],
                notes=apt.get('notes'),
                created_at=apt['created_at'],
                updated_at=apt['updated_at']
            ) for apt in response.appointments
        ]
        future.set_result(appointments)

# API Endpoints
@app.get("/")
async def root():
    return {"message": "API Gateway", "version": "1.0.0"}

@app.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate):
    correlation_id = str(asyncio.urandom(16).hex())
    future = asyncio.Future()
    pending_requests[correlation_id] = future

    command = AppointmentCreateCommand(
        correlation_id=correlation_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_time=appointment.appointment_time,
        duration_minutes=appointment.duration_minutes or 30,
        notes=appointment.notes
    )
    await publish_command(command)

    try:
        result = await asyncio.wait_for(future, timeout=10.0)
        return result
    except asyncio.TimeoutError:
        pending_requests.pop(correlation_id, None)
        raise HTTPException(status_code=504, detail="Request timeout")

@app.get("/appointments", response_model=List[Appointment])
async def list_appointments():
    correlation_id = str(asyncio.urandom(16).hex())
    future = asyncio.Future()
    pending_requests[correlation_id] = future

    command = AppointmentListCommand(correlation_id=correlation_id)
    await publish_command(command)

    try:
        result = await asyncio.wait_for(future, timeout=10.0)
        return result
    except asyncio.TimeoutError:
        pending_requests.pop(correlation_id, None)
        raise HTTPException(status_code=504, detail="Request timeout")

@app.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    correlation_id = str(asyncio.urandom(16).hex())
    future = asyncio.Future()
    pending_requests[correlation_id] = future

    command = AppointmentGetCommand(
        correlation_id=correlation_id,
        appointment_id=appointment_id
    )
    await publish_command(command)

    try:
        result = await asyncio.wait_for(future, timeout=10.0)
        return result
    except asyncio.TimeoutError:
        pending_requests.pop(correlation_id, None)
        raise HTTPException(status_code=404, detail="Appointment not found or timeout")

@app.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, update: AppointmentUpdate):
    correlation_id = str(asyncio.urandom(16).hex())
    future = asyncio.Future()
    pending_requests[correlation_id] = future

    command = AppointmentUpdateCommand(
        correlation_id=correlation_id,
        appointment_id=appointment_id,
        appointment_time=update.appointment_time,
        duration_minutes=update.duration_minutes,
        status=update.status,
        notes=update.notes
    )
    await publish_command(command)

    try:
        result = await asyncio.wait_for(future, timeout=10.0)
        return result
    except asyncio.TimeoutError:
        pending_requests.pop(correlation_id, None)
        raise HTTPException(status_code=504, detail="Request timeout")

@app.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    correlation_id = str(asyncio.urandom(16).hex())
    future = asyncio.Future()
    pending_requests[correlation_id] = future

    command = AppointmentCancelCommand(
        correlation_id=correlation_id,
        appointment_id=appointment_id
    )
    await publish_command(command)

    try:
        result = await asyncio.wait_for(future, timeout=10.0)
        return result
    except asyncio.TimeoutError:
        pending_requests.pop(correlation_id, None)
        raise HTTPException(status_code=504, detail="Request timeout")

# Additional endpoints for patients, etc., can be added similarly

@app.on_event("startup")
async def startup_event():
    await init_nats()

@app.on_event("shutdown")
async def shutdown_event():
    if nats_client:
        await nats_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)