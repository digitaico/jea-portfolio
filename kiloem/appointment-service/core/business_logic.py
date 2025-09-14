"""
Business Logic for Appointment Service
Contains the core business logic for appointment management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from typing import List, Optional
import uuid
from datetime import datetime

from ..models.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentDB
from ...shared.database import add_and_commit
from ...shared.utils import ValidationUtils, TimeUtils


class AppointmentService:
    """Service class for appointment business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_appointment(self, appointment_data: AppointmentCreate) -> Appointment:
        """Create a new appointment with business rules validation"""

        # Validate appointment time is in the future
        if not ValidationUtils.is_future_datetime(appointment_data.appointment_time):
            raise ValueError("Appointment time must be in the future")

        # Validate duration
        if appointment_data.duration_minutes < 15 or appointment_data.duration_minutes > 480:
            raise ValueError("Appointment duration must be between 15 minutes and 8 hours")

        # Check for scheduling conflicts
        conflict = await self._check_availability(
            appointment_data.doctor_id,
            appointment_data.appointment_time,
            appointment_data.duration_minutes
        )
        if conflict:
            raise ValueError("Doctor is not available at this time")

        # Create appointment
        db_appointment = AppointmentDB(
            id=str(uuid.uuid4()),
            patient_id=appointment_data.patient_id,
            doctor_id=appointment_data.doctor_id,
            appointment_time=appointment_data.appointment_time,
            duration_minutes=appointment_data.duration_minutes,
            status="scheduled",
            notes=appointment_data.notes,
            created_at=TimeUtils.now_utc(),
            updated_at=TimeUtils.now_utc()
        )

        await add_and_commit(self.db, db_appointment)

        return Appointment.from_db_model(db_appointment)

    async def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID"""
        result = await self.db.execute(
            select(AppointmentDB).where(AppointmentDB.id == appointment_id)
        )
        db_appointment = result.scalar_one_or_none()

        if db_appointment:
            return Appointment.from_db_model(db_appointment)
        return None

    async def get_all_appointments(self) -> List[Appointment]:
        """Get all appointments"""
        result = await self.db.execute(
            select(AppointmentDB).order_by(AppointmentDB.appointment_time.desc())
        )
        db_appointments = result.scalars().all()

        return [Appointment.from_db_model(apt) for apt in db_appointments]

    async def get_appointments_by_patient(self, patient_id: str) -> List[Appointment]:
        """Get all appointments for a patient"""
        result = await self.db.execute(
            select(AppointmentDB)
            .where(AppointmentDB.patient_id == patient_id)
            .order_by(AppointmentDB.appointment_time.desc())
        )
        db_appointments = result.scalars().all()

        return [Appointment.from_db_model(apt) for apt in db_appointments]

    async def get_appointments_by_doctor(self, doctor_id: str) -> List[Appointment]:
        """Get all appointments for a doctor"""
        result = await self.db.execute(
            select(AppointmentDB)
            .where(AppointmentDB.doctor_id == doctor_id)
            .order_by(AppointmentDB.appointment_time.desc())
        )
        db_appointments = result.scalars().all()

        return [Appointment.from_db_model(apt) for apt in db_appointments]

    async def update_appointment(self, appointment_id: str, update_data: AppointmentUpdate) -> Optional[Appointment]:
        """Update an appointment"""
        # Get existing appointment
        existing = await self.get_appointment_by_id(appointment_id)
        if not existing:
            return None

        # Validate status transition
        if update_data.status and not self._is_valid_status_transition(existing.status, update_data.status):
            raise ValueError(f"Invalid status transition from {existing.status} to {update_data.status}")

        # Check availability if time is being changed
        if update_data.appointment_time:
            duration = update_data.duration_minutes or existing.duration_minutes
            conflict = await self._check_availability(
                existing.doctor_id,
                update_data.appointment_time,
                duration,
                exclude_appointment_id=appointment_id
            )
            if conflict:
                raise ValueError("Doctor is not available at the new time")

        # Prepare update data
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict['updated_at'] = TimeUtils.now_utc()

        # Update in database
        result = await self.db.execute(
            update(AppointmentDB)
            .where(AppointmentDB.id == appointment_id)
            .values(**update_dict)
            .returning(AppointmentDB)
        )

        updated_db = result.scalar_one_or_none()
        if updated_db:
            await self.db.commit()
            return Appointment.from_db_model(updated_db)
        return None

    async def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment"""
        result = await self.db.execute(
            update(AppointmentDB)
            .where(AppointmentDB.id == appointment_id)
            .where(AppointmentDB.status != "cancelled")
            .values(
                status="cancelled",
                updated_at=TimeUtils.now_utc()
            )
        )

        await self.db.commit()
        return result.rowcount > 0

    async def _check_availability(
        self,
        doctor_id: str,
        appointment_time: datetime,
        duration_minutes: int,
        exclude_appointment_id: Optional[str] = None
    ) -> bool:
        """Check if doctor is available at the given time"""
        end_time = appointment_time + timedelta(minutes=duration_minutes)

        # Build query to find conflicting appointments
        query = select(AppointmentDB).where(
            and_(
                AppointmentDB.doctor_id == doctor_id,
                AppointmentDB.status.in_(["scheduled", "confirmed"]),
                or_(
                    and_(
                        AppointmentDB.appointment_time <= appointment_time,
                        AppointmentDB.appointment_time + timedelta(minutes=AppointmentDB.duration_minutes) > appointment_time
                    ),
                    and_(
                        AppointmentDB.appointment_time < end_time,
                        AppointmentDB.appointment_time + timedelta(minutes=AppointmentDB.duration_minutes) >= end_time
                    ),
                    and_(
                        AppointmentDB.appointment_time >= appointment_time,
                        AppointmentDB.appointment_time + timedelta(minutes=AppointmentDB.duration_minutes) <= end_time
                    )
                )
            )
        )

        if exclude_appointment_id:
            query = query.where(AppointmentDB.id != exclude_appointment_id)

        result = await self.db.execute(query)
        conflicts = result.scalars().all()

        return len(conflicts) > 0

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate appointment status transitions"""
        valid_transitions = {
            "scheduled": ["confirmed", "cancelled"],
            "confirmed": ["in_progress", "cancelled"],
            "in_progress": ["completed", "cancelled"],
            "completed": [],  # Terminal state
            "cancelled": [],  # Terminal state
            "no_show": []     # Terminal state
        }

        return new_status in valid_transitions.get(current_status, [])