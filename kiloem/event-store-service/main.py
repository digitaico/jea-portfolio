from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import asyncio
import nats
import os
import json
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, DateTime, Text, select

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db")
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class EventStore(Base):
    __tablename__ = "event_store"

    id = Column(String, primary_key=True)
    subject = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    event_data = Column(Text, nullable=False)
    correlation_id = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_service = Column(String, nullable=True)
    stored_at = Column(DateTime, default=datetime.utcnow)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(title="Event Store Service", version="1.0.0")

# NATS client
nats_client = None
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Pydantic models
class StoredEvent(BaseModel):
    id: str
    subject: str
    event_type: str
    event_data: dict
    correlation_id: Optional[str]
    timestamp: datetime
    source_service: Optional[str]
    stored_at: datetime

class EventQuery(BaseModel):
    subject: Optional[str] = None
    event_type: Optional[str] = None
    correlation_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100

# NATS functions
async def init_nats():
    """Initialize NATS connection and subscribe to all events"""
    global nats_client
    try:
        nats_client = await nats.connect(NATS_URL)
        print(f"Connected to NATS at {NATS_URL}")

        # Subscribe to ALL events using wildcard
        await nats_client.subscribe(">", cb=event_store_handler)
        print("Subscribed to all events: >")

        # Also subscribe to specific patterns for better organization
        await nats_client.subscribe("appointment.*", cb=event_store_handler)
        await nats_client.subscribe("patient.*", cb=event_store_handler)
        await nats_client.subscribe("notification.*", cb=event_store_handler)
        await nats_client.subscribe("doctor.*", cb=event_store_handler)

    except Exception as e:
        print(f"Failed to connect to NATS: {e}")

async def event_store_handler(msg):
    """Handle incoming events and store them"""
    try:
        subject = msg.subject
        event_data = json.loads(msg.data.decode())

        # Extract event metadata
        event_type = event_data.get('event_type', subject)
        correlation_id = event_data.get('correlation_id')
        timestamp = event_data.get('timestamp', datetime.utcnow().isoformat())

        # Store event in database
        async for db in get_db():
            event_store = EventStore(
                id=str(uuid.uuid4()),
                subject=subject,
                event_type=event_type,
                event_data=json.dumps(event_data),
                correlation_id=correlation_id,
                timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if isinstance(timestamp, str) else timestamp,
                source_service=extract_source_service(subject),
                stored_at=datetime.utcnow()
            )

            db.add(event_store)
            await db.commit()
            print(f"📦 Stored event: {subject} -> {event_type}")
            break

    except Exception as e:
        print(f"Error storing event: {e}")

def extract_source_service(subject: str) -> str:
    """Extract source service from subject"""
    if subject.startswith("appointment."):
        return "appointment-service"
    elif subject.startswith("patient."):
        return "patient-service"
    elif subject.startswith("notification."):
        return "notifications-service"
    elif subject.startswith("doctor."):
        return "doctor-service"
    else:
        return "unknown"

@app.get("/")
async def root():
    return {"message": "Event Store Service API", "version": "1.0.0"}

@app.get("/events", response_model=List[StoredEvent])
async def get_events(query: EventQuery = Depends(), db: AsyncSession = Depends(get_db)):
    """Query stored events with filtering"""
    stmt = select(EventStore)

    if query.subject:
        stmt = stmt.where(EventStore.subject == query.subject)
    if query.event_type:
        stmt = stmt.where(EventStore.event_type == query.event_type)
    if query.correlation_id:
        stmt = stmt.where(EventStore.correlation_id == query.correlation_id)
    if query.start_time:
        stmt = stmt.where(EventStore.timestamp >= query.start_time)
    if query.end_time:
        stmt = stmt.where(EventStore.timestamp <= query.end_time)

    stmt = stmt.order_by(EventStore.timestamp.desc()).limit(query.limit)
    result = await db.execute(stmt)
    events = result.scalars().all()

    return [
        StoredEvent(
            id=event.id,
            subject=event.subject,
            event_type=event.event_type,
            event_data=json.loads(event.event_data),
            correlation_id=event.correlation_id,
            timestamp=event.timestamp,
            source_service=event.source_service,
            stored_at=event.stored_at
        )
        for event in events
    ]

@app.get("/events/{event_id}", response_model=StoredEvent)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific event by ID"""
    result = await db.execute(select(EventStore).where(EventStore.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return StoredEvent(
        id=event.id,
        subject=event.subject,
        event_type=event.event_type,
        event_data=json.loads(event.event_data),
        correlation_id=event.correlation_id,
        timestamp=event.timestamp,
        source_service=event.source_service,
        stored_at=event.stored_at
    )

@app.get("/events/correlation/{correlation_id}", response_model=List[StoredEvent])
async def get_events_by_correlation(correlation_id: str, db: AsyncSession = Depends(get_db)):
    """Get all events for a correlation ID (saga/transaction tracking)"""
    result = await db.execute(
        select(EventStore).where(EventStore.correlation_id == correlation_id)
        .order_by(EventStore.timestamp)
    )
    events = result.scalars().all()

    return [
        StoredEvent(
            id=event.id,
            subject=event.subject,
            event_type=event.event_type,
            event_data=json.loads(event.event_data),
            correlation_id=event.correlation_id,
            timestamp=event.timestamp,
            source_service=event.source_service,
            stored_at=event.stored_at
        )
        for event in events
    ]

@app.get("/events/subject/{subject}", response_model=List[StoredEvent])
async def get_events_by_subject(subject: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Get events by subject pattern"""
    result = await db.execute(
        select(EventStore).where(EventStore.subject.like(f"{subject}%"))
        .order_by(EventStore.timestamp.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return [
        StoredEvent(
            id=event.id,
            subject=event.subject,
            event_type=event.event_type,
            event_data=json.loads(event.event_data),
            correlation_id=event.correlation_id,
            timestamp=event.timestamp,
            source_service=event.source_service,
            stored_at=event.stored_at
        )
        for event in events
    ]

@app.get("/stats")
async def get_event_stats(db: AsyncSession = Depends(get_db)):
    """Get event statistics"""
    # Count total events
    result = await db.execute(select(EventStore).with_only_columns([EventStore.id]))
    total_events = len(result.scalars().all())

    # Count by subject
    result = await db.execute("""
        SELECT subject, COUNT(*) as count
        FROM event_store
        GROUP BY subject
        ORDER BY count DESC
    """)
    subject_stats = {row[0]: row[1] for row in result.fetchall()}

    # Count by event type
    result = await db.execute("""
        SELECT event_type, COUNT(*) as count
        FROM event_store
        GROUP BY event_type
        ORDER BY count DESC
    """)
    event_type_stats = {row[0]: row[1] for row in result.fetchall()}

    return {
        "total_events": total_events,
        "by_subject": subject_stats,
        "by_event_type": event_type_stats,
        "timestamp": datetime.utcnow()
    }

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
    uvicorn.run(app, host="0.0.0.0", port=8014)