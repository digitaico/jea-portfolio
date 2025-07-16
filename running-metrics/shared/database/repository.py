from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from shared.database.models import RunningSessionDB, PoseDataDB, RunningMetricsDB

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository class"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @abstractmethod
    async def create(self, obj: T) -> T:
        pass
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        pass
    
    @abstractmethod
    async def update(self, obj: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass


class RunningSessionRepository(BaseRepository[RunningSessionDB]):
    """Repository for running sessions"""
    
    async def create(self, session: RunningSessionDB) -> RunningSessionDB:
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session
    
    async def get_by_id(self, id: UUID) -> Optional[RunningSessionDB]:
        result = await self.session.execute(
            select(RunningSessionDB)
            .options(selectinload(RunningSessionDB.pose_data))
            .options(selectinload(RunningSessionDB.metrics))
            .where(RunningSessionDB.id == id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, session: RunningSessionDB) -> RunningSessionDB:
        await self.session.commit()
        await self.session.refresh(session)
        return session
    
    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            select(RunningSessionDB).where(RunningSessionDB.id == id)
        )
        session = result.scalar_one_or_none()
        if session:
            await self.session.delete(session)
            await self.session.commit()
            return True
        return False
    
    async def get_by_status(self, status: str) -> List[RunningSessionDB]:
        result = await self.session.execute(
            select(RunningSessionDB).where(RunningSessionDB.status == status)
        )
        return result.scalars().all()


class PoseDataRepository(BaseRepository[PoseDataDB]):
    """Repository for pose data"""
    
    async def create(self, pose_data: PoseDataDB) -> PoseDataDB:
        self.session.add(pose_data)
        await self.session.commit()
        await self.session.refresh(pose_data)
        return pose_data
    
    async def get_by_id(self, id: UUID) -> Optional[PoseDataDB]:
        result = await self.session.execute(
            select(PoseDataDB).where(PoseDataDB.id == id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, pose_data: PoseDataDB) -> PoseDataDB:
        await self.session.commit()
        await self.session.refresh(pose_data)
        return pose_data
    
    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            select(PoseDataDB).where(PoseDataDB.id == id)
        )
        pose_data = result.scalar_one_or_none()
        if pose_data:
            await self.session.delete(pose_data)
            await self.session.commit()
            return True
        return False
    
    async def get_by_session_id(self, session_id: UUID) -> List[PoseDataDB]:
        result = await self.session.execute(
            select(PoseDataDB)
            .where(PoseDataDB.session_id == session_id)
            .order_by(PoseDataDB.frame_number)
        )
        return result.scalars().all()


class RunningMetricsRepository(BaseRepository[RunningMetricsDB]):
    """Repository for running metrics"""
    
    async def create(self, metrics: RunningMetricsDB) -> RunningMetricsDB:
        self.session.add(metrics)
        await self.session.commit()
        await self.session.refresh(metrics)
        return metrics
    
    async def get_by_id(self, id: UUID) -> Optional[RunningMetricsDB]:
        result = await self.session.execute(
            select(RunningMetricsDB).where(RunningMetricsDB.id == id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, metrics: RunningMetricsDB) -> RunningMetricsDB:
        await self.session.commit()
        await self.session.refresh(metrics)
        return metrics
    
    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            select(RunningMetricsDB).where(RunningMetricsDB.id == id)
        )
        metrics = result.scalar_one_or_none()
        if metrics:
            await self.session.delete(metrics)
            await self.session.commit()
            return True
        return False
    
    async def get_by_session_id(self, session_id: UUID) -> Optional[RunningMetricsDB]:
        result = await self.session.execute(
            select(RunningMetricsDB).where(RunningMetricsDB.session_id == session_id)
        )
        return result.scalar_one_or_none()