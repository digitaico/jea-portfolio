import asyncio
import nats
import os
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, init_db, Appointment as DBAppointment
from core.business_logic import AppointmentService
from shared.events import (
    AppointmentCreateCommand, AppointmentUpdateCommand, AppointmentCancelCommand,
    AppointmentGetCommand, AppointmentListCommand,
    AppointmentCreatedResponse, AppointmentUpdatedResponse, AppointmentCancelledResponse,
    AppointmentDataResponse, AppointmentListResponse,
    EventSubjects
)

# NATS client
nats_client = None
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


# NATS functions
async def init_nats():
    """Initialize NATS connection"""
    global nats_client
    try:
        nats_client = await nats.connect(NATS_URL)
        print(f"Connected to NATS at {NATS_URL}")

        # Subscribe to command events
        await nats_client.subscribe(EventSubjects.APPOINTMENT_CREATE_COMMAND, cb=handle_create_appointment)
        await nats_client.subscribe(EventSubjects.APPOINTMENT_UPDATE_COMMAND, cb=handle_update_appointment)
        await nats_client.subscribe(EventSubjects.APPOINTMENT_CANCEL_COMMAND, cb=handle_cancel_appointment)
        await nats_client.subscribe(EventSubjects.APPOINTMENT_GET_COMMAND, cb=handle_get_appointment)
        await nats_client.subscribe(EventSubjects.APPOINTMENT_LIST_COMMAND, cb=handle_list_appointments)

    except Exception as e:
        print(f"Failed to connect to NATS: {e}")

async def publish_response(response):
    """Publish response event to NATS"""
    if nats_client:
        try:
            event_data = response.model_dump_json()
            await nats_client.publish(response.event_type, event_data.encode())
            print(f"Published response: {response.event_type}")
        except Exception as e:
            print(f"Failed to publish response: {e}")

# Command handlers
async def handle_create_appointment(msg):
    """Handle appointment creation command"""
    try:
        data = json.loads(msg.data.decode())
        command = AppointmentCreateCommand(**data)

        async for db in get_db():
            service = AppointmentService(db)
            appointment = await service.create_appointment_from_command(command)

            response = AppointmentCreatedResponse(
                correlation_id=command.correlation_id,
                appointment_id=appointment.id,
                patient_id=appointment.patient_id,
                doctor_id=appointment.doctor_id,
                appointment_time=appointment.appointment_time,
                duration_minutes=appointment.duration_minutes,
                status=appointment.status,
                notes=appointment.notes,
                created_at=appointment.created_at,
                updated_at=appointment.updated_at
            )
            await publish_response(response)
            break
    except Exception as e:
        print(f"Error handling create appointment: {e}")

async def handle_update_appointment(msg):
    """Handle appointment update command"""
    try:
        data = json.loads(msg.data.decode())
        command = AppointmentUpdateCommand(**data)

        async for db in get_db():
            service = AppointmentService(db)
            appointment = await service.update_appointment_from_command(command)

            if appointment:
                response = AppointmentUpdatedResponse(
                    correlation_id=command.correlation_id,
                    appointment_id=appointment.id,
                    patient_id=appointment.patient_id,
                    doctor_id=appointment.doctor_id,
                    appointment_time=appointment.appointment_time,
                    duration_minutes=appointment.duration_minutes,
                    status=appointment.status,
                    notes=appointment.notes,
                    created_at=appointment.created_at,
                    updated_at=appointment.updated_at
                )
                await publish_response(response)
            break
    except Exception as e:
        print(f"Error handling update appointment: {e}")

async def handle_cancel_appointment(msg):
    """Handle appointment cancellation command"""
    try:
        data = json.loads(msg.data.decode())
        command = AppointmentCancelCommand(**data)

        async for db in get_db():
            service = AppointmentService(db)
            success = await service.cancel_appointment(command.appointment_id)

            if success:
                response = AppointmentCancelledResponse(
                    correlation_id=command.correlation_id,
                    appointment_id=command.appointment_id
                )
                await publish_response(response)
            break
    except Exception as e:
        print(f"Error handling cancel appointment: {e}")

async def handle_get_appointment(msg):
    """Handle get appointment command"""
    try:
        data = json.loads(msg.data.decode())
        command = AppointmentGetCommand(**data)

        async for db in get_db():
            service = AppointmentService(db)
            appointment = await service.get_appointment_by_id(command.appointment_id)

            if appointment:
                response = AppointmentDataResponse(
                    correlation_id=command.correlation_id,
                    appointment_id=appointment.id,
                    patient_id=appointment.patient_id,
                    doctor_id=appointment.doctor_id,
                    appointment_time=appointment.appointment_time,
                    duration_minutes=appointment.duration_minutes,
                    status=appointment.status,
                    notes=appointment.notes,
                    created_at=appointment.created_at,
                    updated_at=appointment.updated_at
                )
                await publish_response(response)
            break
    except Exception as e:
        print(f"Error handling get appointment: {e}")

async def handle_list_appointments(msg):
    """Handle list appointments command"""
    try:
        data = json.loads(msg.data.decode())
        command = AppointmentListCommand(**data)

        async for db in get_db():
            service = AppointmentService(db)
            appointments = await service.get_all_appointments()

            appointment_list = [
                {
                    "id": apt.id,
                    "patient_id": apt.patient_id,
                    "doctor_id": apt.doctor_id,
                    "appointment_time": apt.appointment_time.isoformat(),
                    "duration_minutes": apt.duration_minutes,
                    "status": apt.status,
                    "notes": apt.notes,
                    "created_at": apt.created_at.isoformat(),
                    "updated_at": apt.updated_at.isoformat()
                }
                for apt in appointments
            ]

            response = AppointmentListResponse(
                correlation_id=command.correlation_id,
                appointments=appointment_list
            )
            await publish_response(response)
            break
    except Exception as e:
        print(f"Error handling list appointments: {e}")

async def main():
    """Main function to run the service"""
    await init_db()
    await init_nats()

    # Keep the service running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        if nats_client:
            await nats_client.close()

if __name__ == "__main__":
    asyncio.run(main())