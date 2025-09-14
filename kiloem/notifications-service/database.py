from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, DateTime, Text
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)
    appointment_id = Column(String, nullable=False)
    type = Column(String, nullable=False)  # email, sms, push
    message = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, sent, failed
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)