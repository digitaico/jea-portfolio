#!/usr/bin/env python3
"""
Event Bus for microservices architecture.

This service handles event publishing, subscription, and routing
between microservices using Redis Pub/Sub.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.models import Event, EventType, EventStatus, APIResponse, ServiceHealth
from shared.utils import Logger, RedisManager, ServiceHealth as HealthMonitor


# Initialize logger
logger = Logger("event-bus", os.getenv("LOG_LEVEL", "INFO"))

# Initialize Redis manager
redis_manager = RedisManager(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Event storage (in production, use a proper database)
events_storage = []

# WebSocket connections for real-time event streaming
websocket_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Event Bus")
    
    # Start event processing task
    event_processor_task = asyncio.create_task(process_events())
    
    yield
    
    # Cleanup
    event_processor_task.cancel()
    logger.info("Shutting down Event Bus")


# Create FastAPI app
app = FastAPI(
    title="Event Bus",
    description="Event bus for microservices communication",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EventPublishRequest(BaseModel):
    """Event publish request model."""
    type: EventType
    data: Dict[str, Any]
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


class EventSubscriptionRequest(BaseModel):
    """Event subscription request model."""
    event_types: Optional[List[EventType]] = None
    user_id: Optional[str] = None


class EventBus:
    """Event bus implementation."""
    
    def __init__(self):
        self.redis_manager = redis_manager
        self.event_handlers = {}
        self.subscribers = {}
    
    async def publish_event(self, event: Event) -> bool:
        """Publish event to Redis."""
        try:
            # Store event
            events_storage.append(event.dict())
            
            # Keep only last 1000 events
            if len(events_storage) > 1000:
                events_storage.pop(0)
            
            # Publish to Redis
            success = self.redis_manager.publish_event("event_bus", event.dict())
            
            if success:
                logger.info(f"Event published: {event.type} by {event.source}")
                
                # Notify WebSocket connections
                await self.notify_websockets(event)
            else:
                logger.error(f"Failed to publish event: {event.type}")
            
            return success
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False
    
    async def subscribe_to_events(self, event_types: List[EventType] = None, 
                                user_id: str = None) -> List[Event]:
        """Subscribe to events."""
        try:
            pubsub = self.redis_manager.subscribe_to_channel("event_bus")
            events = []
            
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        event = Event(**event_data)
                        
                        # Filter by event type
                        if event_types and event.type not in event_types:
                            continue
                        
                        # Filter by user ID
                        if user_id and event.user_id != user_id:
                            continue
                        
                        events.append(event)
                        
                        # Return events in batches
                        if len(events) >= 10:
                            yield events
                            events = []
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode event: {e}")
        except Exception as e:
            logger.error(f"Error subscribing to events: {e}")
    
    async def notify_websockets(self, event: Event):
        """Notify WebSocket connections of new events."""
        if not websocket_connections:
            return
        
        event_data = event.dict()
        event_json = json.dumps(event_data)
        
        # Send to all connected WebSocket clients
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_text(event_json)
            except Exception as e:
                logger.error(f"Failed to send to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected WebSockets
        for websocket in disconnected:
            websocket_connections.remove(websocket)
    
    def get_recent_events(self, limit: int = 100, 
                         event_types: List[EventType] = None,
                         user_id: str = None) -> List[Event]:
        """Get recent events."""
        events = events_storage.copy()
        
        # Filter by event type
        if event_types:
            events = [e for e in events if e["type"] in event_types]
        
        # Filter by user ID
        if user_id:
            events = [e for e in events if e.get("user_id") == user_id]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit results
        return events[:limit]


# Initialize event bus
event_bus = EventBus()


async def process_events():
    """Background task to process events."""
    logger.info("Starting event processor")
    
    try:
        async for events in event_bus.subscribe_to_events():
            for event in events:
                # Process event based on type
                await process_event(event)
    except asyncio.CancelledError:
        logger.info("Event processor cancelled")
    except Exception as e:
        logger.error(f"Event processor error: {e}")


async def process_event(event: Event):
    """Process individual event."""
    try:
        logger.info(f"Processing event: {event.type}")
        
        # Update event status
        event.status = EventStatus.PROCESSING
        
        # Handle different event types
        if event.type == EventType.USER_CREATED:
            await handle_user_created(event)
        elif event.type == EventType.IMAGE_PROCESSING_COMPLETED:
            await handle_image_processing_completed(event)
        elif event.type == EventType.IMAGE_PROCESSING_FAILED:
            await handle_image_processing_failed(event)
        else:
            logger.info(f"No specific handler for event type: {event.type}")
        
        # Mark event as completed
        event.status = EventStatus.COMPLETED
        
    except Exception as e:
        logger.error(f"Error processing event {event.id}: {e}")
        event.status = EventStatus.FAILED


async def handle_user_created(event: Event):
    """Handle user created event."""
    logger.info(f"Handling user created event: {event.data}")
    # Send welcome notification, etc.


async def handle_image_processing_completed(event: Event):
    """Handle image processing completed event."""
    logger.info(f"Handling image processing completed: {event.data}")
    # Send notification to user, update statistics, etc.


async def handle_image_processing_failed(event: Event):
    """Handle image processing failed event."""
    logger.info(f"Handling image processing failed: {event.data}")
    # Send error notification to user, log error, etc.


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint."""
    return APIResponse(
        success=True,
        message="Event Bus is running",
        data={
            "service": "event-bus",
            "version": "1.0.0",
            "status": "healthy"
        }
    )


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Health check endpoint."""
    health = HealthMonitor("event-bus", "1.0.0")
    return health.get_health()


@app.post("/events/publish")
async def publish_event(request: EventPublishRequest):
    """Publish an event."""
    try:
        event = Event(
            id=str(uuid.uuid4()),
            type=request.type,
            source="event-bus",
            timestamp=datetime.utcnow(),
            data=request.data,
            status=EventStatus.PENDING,
            correlation_id=request.correlation_id,
            user_id=request.user_id
        )
        
        success = await event_bus.publish_event(event)
        
        if success:
            return APIResponse(
                success=True,
                message="Event published successfully",
                data=event.dict()
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to publish event")
            
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events")
async def get_events(limit: int = 100, 
                    event_type: Optional[EventType] = None,
                    user_id: Optional[str] = None):
    """Get recent events."""
    try:
        event_types = [event_type] if event_type else None
        events = event_bus.get_recent_events(limit, event_types, user_id)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(events)} events",
            data={"events": events}
        )
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}")
async def get_event(event_id: str):
    """Get specific event by ID."""
    try:
        for event in events_storage:
            if event["id"] == event_id:
                return APIResponse(
                    success=True,
                    message="Event found",
                    data=event
                )
        
        raise HTTPException(status_code=404, detail="Event not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        logger.info("WebSocket client connected")
        
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to Event Bus",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client message (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


@app.get("/stats")
async def get_stats():
    """Get event bus statistics."""
    try:
        total_events = len(events_storage)
        event_types_count = {}
        
        for event in events_storage:
            event_type = event["type"]
            event_types_count[event_type] = event_types_count.get(event_type, 0) + 1
        
        stats = {
            "total_events": total_events,
            "event_types_count": event_types_count,
            "active_websocket_connections": len(websocket_connections),
            "uptime": "N/A"  # Would need to track start time
        }
        
        return APIResponse(
            success=True,
            message="Event bus statistics",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/events/clear")
async def clear_events():
    """Clear all events (admin only)."""
    try:
        global events_storage
        events_storage.clear()
        
        return APIResponse(
            success=True,
            message="All events cleared"
        )
    except Exception as e:
        logger.error(f"Error clearing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
