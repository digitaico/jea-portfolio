"""
API Routes for Appointment Service
Contains all FastAPI route definitions for appointment management.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from datetime import datetime

from ..models.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from ..core.business_logic import AppointmentService
from ...shared.database import get_db
from ...shared.nats_client import nats_client, publish_domain_event
from ...shared.events import EventSubjects

router = APIRouter()

@router.get("/")
async def root():
    """Service health check endpoint"""
    return {"message": "Appointment Service API", "version": "1.0.0"}

@router.post("/appointments", response_model=Appointment)
async def create_appointment(
    appointment: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new appointment"""
    service = AppointmentService(db)

    # Create appointment
    new_appointment = await service.create_appointment(appointment)

    # Publish event
    correlation_id = await publish_domain_event(
        EventSubjects.APPOINTMENT_SCHEDULED,
        "appointment.scheduled",
        {
            "appointment_id": new_appointment.id,
            "patient_id": new_appointment.patient_id,
            "doctor_id": new_appointment.doctor_id,
            "appointment_time": new_appointment.appointment_time.isoformat(),
            "duration_minutes": new_appointment.duration_minutes,
            "status": new_appointment.status,
            "notes": new_appointment.notes
        }
    )

    return new_appointment

@router.get("/appointments", response_model=List[Appointment])
async def list_appointments(db: AsyncSession = Depends(get_db)):
    """List all appointments"""
    service = AppointmentService(db)
    return await service.get_all_appointments()

@router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific appointment"""
    service = AppointmentService(db)
    appointment = await service.get_appointment_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(
    appointment_id: str,
    update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an appointment"""
    service = AppointmentService(db)
    appointment = await service.update_appointment(appointment_id, update)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Publish event
    await publish_domain_event(
        EventSubjects.APPOINTMENT_UPDATED,
        "appointment.updated",
        {
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "appointment_time": appointment.appointment_time.isoformat(),
            "duration_minutes": appointment.duration_minutes,
            "status": appointment.status,
            "notes": appointment.notes
        }
    )

    return appointment

@router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel an appointment"""
    service = AppointmentService(db)
    success = await service.cancel_appointment(appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Publish event
    await publish_domain_event(
        EventSubjects.APPOINTMENT_CANCELLED,
        "appointment.cancelled",
        {"appointment_id": appointment_id}
    )

    return {"message": "Appointment cancelled", "id": appointment_id}

@router.get("/appointments/patient/{patient_id}", response_model=List[Appointment])
async def get_patient_appointments(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get all appointments for a patient"""
    service = AppointmentService(db)
    return await service.get_appointments_by_patient(patient_id)

@router.get("/appointments/doctor/{doctor_id}", response_model=List[Appointment])
async def get_doctor_appointments(doctor_id: str, db: AsyncSession = Depends(get_db)):
    """Get all appointments for a doctor"""
    service = AppointmentService(db)
    return await service.get_appointments_by_doctor(doctor_id)