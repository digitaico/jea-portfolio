"""
Shared Repositories Module
Provides data access layer with SQL queries separated from business logic.
Uses Repository pattern for clean data operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .database import Base
from .events import (
    AppointmentEvent, PatientEvent, NotificationEvent,
    EventStoreEvent, EventSubjects
)

# Base Repository Class
class BaseRepository:
    """Base repository with common CRUD operations"""

    def __init__(self, session: AsyncSession, model_class):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: str):
        """Get entity by ID"""
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0):
        """Get all entities with pagination"""
        result = await self.session.execute(
            select(self.model_class)
            .order_by(desc(self.model_class.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(self, **kwargs):
        """Create new entity"""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: str, **kwargs):
        """Update entity by ID"""
        kwargs['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
            .returning(self.model_class)
        )
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, id: str) -> bool:
        """Delete entity by ID"""
        result = await self.session.execute(
            delete(self.model_class).where(self.model_class.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0

# Appointment Repository
class AppointmentRepository(BaseRepository):
    """Repository for appointment operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, None)  # We'll define model in service-specific repo

    async def get_by_patient_id(self, patient_id: str) -> List:
        """Get appointments by patient ID"""
        # This would be implemented in service-specific repository
        pass

    async def get_by_doctor_id(self, doctor_id: str) -> List:
        """Get appointments by doctor ID"""
        # This would be implemented in service-specific repository
        pass

    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List:
        """Get appointments within date range"""
        # This would be implemented in service-specific repository
        pass

    async def get_conflicting_appointments(self, doctor_id: str, start_time: datetime, duration: int) -> List:
        """Get conflicting appointments for doctor"""
        # This would be implemented in service-specific repository
        pass

# Patient Repository
class PatientRepository(BaseRepository):
    """Repository for patient operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, None)  # We'll define model in service-specific repo

    async def find_by_email(self, email: str):
        """Find patient by email"""
        # This would be implemented in service-specific repository
        pass

    async def find_by_phone(self, phone: str):
        """Find patient by phone"""
        # This would be implemented in service-specific repository
        pass

    async def search_by_name(self, name_pattern: str) -> List:
        """Search patients by name pattern"""
        # This would be implemented in service-specific repository
        pass

# Notification Repository
class NotificationRepository(BaseRepository):
    """Repository for notification operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, None)  # We'll define model in service-specific repo

    async def get_by_appointment_id(self, appointment_id: str) -> List:
        """Get notifications for appointment"""
        # This would be implemented in service-specific repository
        pass

    async def get_by_patient_id(self, patient_id: str) -> List:
        """Get notifications for patient"""
        # This would be implemented in service-specific repository
        pass

    async def get_pending_notifications(self) -> List:
        """Get pending notifications"""
        # This would be implemented in service-specific repository
        pass

# Event Store Repository
class EventStoreRepository(BaseRepository):
    """Repository for event store operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, None)  # We'll define model in service-specific repo

    async def get_events_by_subject(self, subject: str, limit: int = 100) -> List:
        """Get events by subject pattern"""
        # This would be implemented in service-specific repository
        pass

    async def get_events_by_correlation_id(self, correlation_id: str) -> List:
        """Get events by correlation ID for saga tracking"""
        # This would be implemented in service-specific repository
        pass

    async def get_events_by_time_range(self, start_time: datetime, end_time: datetime) -> List:
        """Get events within time range"""
        # This would be implemented in service-specific repository
        pass

    async def get_event_statistics(self) -> Dict[str, Any]:
        """Get event statistics"""
        # This would be implemented in service-specific repository
        pass

# Repository Factory
class RepositoryFactory:
    """Factory for creating repository instances"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def get_appointment_repository(self) -> AppointmentRepository:
        return AppointmentRepository(self.session)

    def get_patient_repository(self) -> PatientRepository:
        return PatientRepository(self.session)

    def get_notification_repository(self) -> NotificationRepository:
        return NotificationRepository(self.session)

    def get_event_store_repository(self) -> EventStoreRepository:
        return EventStoreRepository(self.session)

# Query Builders for Complex Operations
class QueryBuilder:
    """Helper class for building complex queries"""

    @staticmethod
    def build_appointment_filter_query(
        patient_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """Build complex appointment filter query"""
        conditions = []

        if patient_id:
            conditions.append(f"patient_id = '{patient_id}'")
        if doctor_id:
            conditions.append(f"doctor_id = '{doctor_id}'")
        if status:
            conditions.append(f"status = '{status}'")
        if start_date:
            conditions.append(f"appointment_time >= '{start_date.isoformat()}'")
        if end_date:
            conditions.append(f"appointment_time <= '{end_date.isoformat()}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return f"""
        SELECT * FROM appointments
        WHERE {where_clause}
        ORDER BY appointment_time DESC
        """

    @staticmethod
    def build_event_correlation_query(correlation_id: str):
        """Build query to get all events for a correlation ID"""
        return f"""
        SELECT * FROM event_store
        WHERE correlation_id = '{correlation_id}'
        ORDER BY timestamp ASC
        """

# Transaction Management
class UnitOfWork:
    """Unit of Work pattern for transaction management"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()

    async def commit(self):
        """Explicitly commit transaction"""
        await self.session.commit()

    async def rollback(self):
        """Explicitly rollback transaction"""
        await self.session.rollback()