#!/usr/bin/env python3
"""
Notification Service for microservices architecture.

This service handles notifications, email sending, and real-time
notifications to users.
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.models import (
    Notification, Event, EventType, EventStatus,
    APIResponse, ServiceHealth
)
from shared.utils import Logger, EventBus, ServiceHealth as HealthMonitor


# Initialize logger
logger = Logger("notification-service", os.getenv("LOG_LEVEL", "INFO"))

# Initialize event bus
event_bus = EventBus(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# In-memory storage (in production, use a database)
notifications = {}

# WebSocket connections for real-time notifications
websocket_connections: Dict[str, List[WebSocket]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Notification Service")
    
    # Start event processing task
    event_processor_task = asyncio.create_task(process_events())
    
    yield
    
    # Cleanup
    event_processor_task.cancel()
    logger.info("Shutting down Notification Service")


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Service for notifications and messaging",
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


class NotificationCreate(BaseModel):
    """Notification creation model."""
    user_id: str
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class NotificationUpdate(BaseModel):
    """Notification update model."""
    title: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


async def process_events():
    """Background task to process events and create notifications."""
    logger.info("Starting event processor")
    
    try:
        async for events in event_bus.subscribe_to_events():
            for event in events:
                await process_event(event)
    except asyncio.CancelledError:
        logger.info("Event processor cancelled")
    except Exception as e:
        logger.error(f"Event processor error: {e}")


async def process_event(event: Event):
    """Process individual event and create notifications."""
    try:
        logger.info(f"Processing event: {event.type}")
        
        # Handle different event types
        if event.type == EventType.USER_CREATED:
            await handle_user_created(event)
        elif event.type == EventType.IMAGE_PROCESSING_COMPLETED:
            await handle_image_processing_completed(event)
        elif event.type == EventType.IMAGE_PROCESSING_FAILED:
            await handle_image_processing_failed(event)
        elif event.type == EventType.USER_LOGIN:
            await handle_user_login(event)
        else:
            logger.info(f"No specific handler for event type: {event.type}")
        
    except Exception as e:
        logger.error(f"Error processing event {event.id}: {e}")


async def handle_user_created(event: Event):
    """Handle user created event."""
    try:
        user_id = event.data.get("user_id")
        if not user_id:
            return
        
        # Create welcome notification
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="welcome",
            title="Welcome to our platform!",
            message="Thank you for joining us. We're excited to have you on board!",
            data={"event_id": event.id},
            status="pending",
            created_at=datetime.utcnow()
        )
        
        notifications[notification.id] = notification.dict()
        
        # Send real-time notification
        await send_real_time_notification(user_id, notification)
        
        # Publish notification sent event
        await event_bus.publish_event(
            EventType.NOTIFICATION_SENT,
            {
                "notification_id": notification.id,
                "user_id": user_id,
                "type": notification.type
            },
            user_id=user_id
        )
        
        logger.info(f"Welcome notification created for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling user created event: {e}")


async def handle_image_processing_completed(event: Event):
    """Handle image processing completed event."""
    try:
        user_id = event.data.get("user_id")
        upload_id = event.data.get("upload_id")
        transformation_type = event.data.get("transformation_type")
        
        if not user_id:
            return
        
        # Create completion notification
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="image_processing_completed",
            title="Image Processing Completed",
            message=f"Your image has been successfully processed with {transformation_type} transformation.",
            data={
                "event_id": event.id,
                "upload_id": upload_id,
                "transformation_type": transformation_type
            },
            status="pending",
            created_at=datetime.utcnow()
        )
        
        notifications[notification.id] = notification.dict()
        
        # Send real-time notification
        await send_real_time_notification(user_id, notification)
        
        # Publish notification sent event
        await event_bus.publish_event(
            EventType.NOTIFICATION_SENT,
            {
                "notification_id": notification.id,
                "user_id": user_id,
                "type": notification.type
            },
            user_id=user_id
        )
        
        logger.info(f"Processing completed notification created for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling image processing completed event: {e}")


async def handle_image_processing_failed(event: Event):
    """Handle image processing failed event."""
    try:
        user_id = event.data.get("user_id")
        upload_id = event.data.get("upload_id")
        transformation_type = event.data.get("transformation_type")
        error = event.data.get("error", "Unknown error")
        
        if not user_id:
            return
        
        # Create failure notification
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="image_processing_failed",
            title="Image Processing Failed",
            message=f"Sorry, your image processing with {transformation_type} transformation failed: {error}",
            data={
                "event_id": event.id,
                "upload_id": upload_id,
                "transformation_type": transformation_type,
                "error": error
            },
            status="pending",
            created_at=datetime.utcnow()
        )
        
        notifications[notification.id] = notification.dict()
        
        # Send real-time notification
        await send_real_time_notification(user_id, notification)
        
        # Publish notification sent event
        await event_bus.publish_event(
            EventType.NOTIFICATION_SENT,
            {
                "notification_id": notification.id,
                "user_id": user_id,
                "type": notification.type
            },
            user_id=user_id
        )
        
        logger.info(f"Processing failed notification created for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling image processing failed event: {e}")


async def handle_user_login(event: Event):
    """Handle user login event."""
    try:
        user_id = event.data.get("user_id")
        if not user_id:
            return
        
        # Create login notification (optional - for security)
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="login",
            title="Login Successful",
            message="You have successfully logged into your account.",
            data={
                "event_id": event.id,
                "login_time": event.data.get("login_time")
            },
            status="pending",
            created_at=datetime.utcnow()
        )
        
        notifications[notification.id] = notification.dict()
        
        # Send real-time notification
        await send_real_time_notification(user_id, notification)
        
        logger.info(f"Login notification created for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling user login event: {e}")


async def send_real_time_notification(user_id: str, notification: Notification):
    """Send real-time notification via WebSocket."""
    if user_id not in websocket_connections:
        return
    
    notification_data = notification.dict()
    notification_json = json.dumps(notification_data)
    
    # Send to all connected WebSocket clients for this user
    disconnected = []
    for websocket in websocket_connections[user_id]:
        try:
            await websocket.send_text(notification_json)
        except Exception as e:
            logger.error(f"Failed to send to WebSocket: {e}")
            disconnected.append(websocket)
    
    # Remove disconnected WebSockets
    for websocket in disconnected:
        websocket_connections[user_id].remove(websocket)


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint."""
    return APIResponse(
        success=True,
        message="Notification Service is running",
        data={
            "service": "notification-service",
            "version": "1.0.0",
            "status": "healthy"
        }
    )


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Health check endpoint."""
    health = HealthMonitor("notification-service", "1.0.0")
    return health.get_health()


@app.post("/notifications", response_model=APIResponse)
async def create_notification(notification_data: NotificationCreate):
    """Create a new notification."""
    try:
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=notification_data.user_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            data=notification_data.data or {},
            status="pending",
            created_at=datetime.utcnow()
        )
        
        notifications[notification.id] = notification.dict()
        
        # Send real-time notification
        await send_real_time_notification(notification.user_id, notification)
        
        # Publish notification sent event
        await event_bus.publish_event(
            EventType.NOTIFICATION_SENT,
            {
                "notification_id": notification.id,
                "user_id": notification.user_id,
                "type": notification.type
            },
            user_id=notification.user_id
        )
        
        logger.info(f"Notification created: {notification.id} for user {notification.user_id}")
        
        return APIResponse(
            success=True,
            message="Notification created successfully",
            data=notification.dict()
        )
        
    except Exception as e:
        logger.error(f"Create notification failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")


@app.get("/notifications", response_model=APIResponse)
async def list_notifications(
    user_id: str,
    page: int = 1,
    size: int = 10,
    notification_type: Optional[str] = None,
    unread_only: bool = False
):
    """List notifications for a user."""
    try:
        # Filter notifications by user
        user_notifications = [
            n for n in notifications.values()
            if n["user_id"] == user_id
        ]
        
        # Filter by type
        if notification_type:
            user_notifications = [
                n for n in user_notifications
                if n["type"] == notification_type
            ]
        
        # Filter unread only
        if unread_only:
            user_notifications = [
                n for n in user_notifications
                if not n.get("read_at")
            ]
        
        # Sort by creation date (newest first)
        user_notifications.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        total = len(user_notifications)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_notifications = user_notifications[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_notifications)} notifications",
            data={
                "notifications": paginated_notifications,
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
        )
        
    except Exception as e:
        logger.error(f"List notifications failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list notifications")


@app.get("/notifications/{notification_id}", response_model=APIResponse)
async def get_notification(notification_id: str, user_id: str):
    """Get a specific notification."""
    try:
        if notification_id not in notifications:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification = notifications[notification_id]
        
        # Check if user owns the notification
        if notification["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return APIResponse(
            success=True,
            message="Notification retrieved successfully",
            data=notification
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get notification failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification")


@app.put("/notifications/{notification_id}/read", response_model=APIResponse)
async def mark_notification_read(notification_id: str, user_id: str):
    """Mark a notification as read."""
    try:
        if notification_id not in notifications:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification = notifications[notification_id]
        
        # Check if user owns the notification
        if notification["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Mark as read
        notification["read_at"] = datetime.utcnow()
        notification["status"] = "read"
        
        logger.info(f"Notification marked as read: {notification_id}")
        
        return APIResponse(
            success=True,
            message="Notification marked as read"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark notification read failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")


@app.delete("/notifications/{notification_id}", response_model=APIResponse)
async def delete_notification(notification_id: str, user_id: str):
    """Delete a notification."""
    try:
        if notification_id not in notifications:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification = notifications[notification_id]
        
        # Check if user owns the notification
        if notification["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete notification
        del notifications[notification_id]
        
        logger.info(f"Notification deleted: {notification_id}")
        
        return APIResponse(
            success=True,
            message="Notification deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete notification failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications."""
    await websocket.accept()
    
    # Add to user's WebSocket connections
    if user_id not in websocket_connections:
        websocket_connections[user_id] = []
    websocket_connections[user_id].append(websocket)
    
    try:
        logger.info(f"WebSocket client connected for user: {user_id}")
        
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to Notification Service",
            "user_id": user_id,
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
                logger.info(f"WebSocket client disconnected for user: {user_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
                break
                
    finally:
        # Remove from user's WebSocket connections
        if user_id in websocket_connections and websocket in websocket_connections[user_id]:
            websocket_connections[user_id].remove(websocket)
            if not websocket_connections[user_id]:
                del websocket_connections[user_id]


@app.get("/stats")
async def get_notification_stats():
    """Get notification statistics."""
    try:
        total_notifications = len(notifications)
        unread_notifications = len([
            n for n in notifications.values()
            if not n.get("read_at")
        ])
        
        type_counts = {}
        for notification in notifications.values():
            notification_type = notification["type"]
            type_counts[notification_type] = type_counts.get(notification_type, 0) + 1
        
        stats = {
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
            "type_distribution": type_counts,
            "active_websocket_connections": sum(len(conns) for conns in websocket_connections.values())
        }
        
        return APIResponse(
            success=True,
            message="Notification statistics",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Get notification stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification statistics")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
