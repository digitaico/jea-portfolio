#!/usr/bin/env python3
"""
Stage 6: Advanced Real-Time Features
====================================

This stage demonstrates real-time communication features:
- Server-Sent Events (SSE) for real-time progress updates
- WebSocket connections for live transformation status
- Progress tracking for long-running operations
- Real-time notifications and updates

This builds upon all previous stages while adding new capabilities.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis.asyncio as redis

# Import from previous stages
from image_transformer import ImageColorTransformer
from database import db_manager, TransformationHistory
from config import settings


class TransformationStatus(Enum):
    """Status of image transformation."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TransformationProgress:
    """Progress tracking for transformations."""
    id: str
    status: TransformationStatus
    progress: int  # 0-100
    message: str
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    current_step: str = ""
    total_steps: int = 1
    current_step_number: int = 0


class RealtimeTransformationManager:
    """Manages real-time transformation tracking and notifications."""
    
    def __init__(self):
        self.active_transformations: Dict[str, TransformationProgress] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.websocket_connections: List[WebSocket] = []
    
    async def initialize_redis(self):
        """Initialize Redis connection for pub/sub."""
        try:
            self.redis_client = redis.Redis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                decode_responses=True
            )
            await self.redis_client.ping()
            print("✅ Redis connection established for real-time features")
        except Exception as e:
            print(f"⚠️  Redis not available: {e}")
            self.redis_client = None
    
    async def create_transformation(self, image_path: str, transformation_type: str) -> str:
        """Create a new transformation with real-time tracking."""
        transformation_id = str(uuid.uuid4())
        
        progress = TransformationProgress(
            id=transformation_id,
            status=TransformationStatus.PENDING,
            progress=0,
            message="Transformation queued",
            start_time=datetime.now(),
            current_step="Initializing",
            total_steps=3
        )
        
        self.active_transformations[transformation_id] = progress
        
        # Publish to Redis for real-time updates
        if self.redis_client:
            await self.redis_client.publish(
                "transformation_updates",
                json.dumps(asdict(progress), default=str)
            )
        
        return transformation_id
    
    async def update_progress(self, transformation_id: str, progress: int, 
                            message: str, current_step: str = None):
        """Update transformation progress."""
        if transformation_id in self.active_transformations:
            transformation = self.active_transformations[transformation_id]
            transformation.progress = progress
            transformation.message = message
            transformation.current_step = current_step or transformation.current_step
            transformation.current_step_number = int(progress / 100 * transformation.total_steps)
            
            # Publish update to Redis
            if self.redis_client:
                await self.redis_client.publish(
                    "transformation_updates",
                    json.dumps(asdict(transformation), default=str)
                )
            
            # Send to WebSocket connections
            await self.broadcast_to_websockets(asdict(transformation))
    
    async def complete_transformation(self, transformation_id: str, success: bool = True):
        """Mark transformation as completed."""
        if transformation_id in self.active_transformations:
            transformation = self.active_transformations[transformation_id]
            transformation.status = TransformationStatus.COMPLETED if success else TransformationStatus.FAILED
            transformation.progress = 100 if success else 0
            transformation.message = "Transformation completed" if success else "Transformation failed"
            
            # Publish final update
            if self.redis_client:
                await self.redis_client.publish(
                    "transformation_updates",
                    json.dumps(asdict(transformation), default=str)
                )
            
            # Send to WebSocket connections
            await self.broadcast_to_websockets(asdict(transformation))
            
            # Clean up after delay
            await asyncio.sleep(5)
            if transformation_id in self.active_transformations:
                del self.active_transformations[transformation_id]
    
    async def broadcast_to_websockets(self, data: Dict[str, Any]):
        """Broadcast data to all connected WebSocket clients."""
        if not self.websocket_connections:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected.append(websocket)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)


# Global instance
realtime_manager = RealtimeTransformationManager()


# Pydantic models for API
class TransformationRequest(BaseModel):
    transformation_type: str
    parameters: Optional[Dict[str, Any]] = {}
    output_format: Optional[str] = "jpg"


class TransformationResponse(BaseModel):
    transformation_id: str
    status: str
    message: str
    progress: int


# FastAPI app for Stage 6
app = FastAPI(
    title="Stage 6: Real-Time Image Processing API",
    description="Advanced real-time features with SSE, WebSockets, and progress tracking",
    version="6.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize real-time features on startup."""
    await realtime_manager.initialize_redis()


@app.get("/")
async def root():
    """Health check with real-time features status."""
    return {
        "stage": 6,
        "name": "Real-Time Image Processing API",
        "features": [
            "Server-Sent Events (SSE)",
            "WebSocket connections",
            "Real-time progress tracking",
            "Redis pub/sub integration",
            "Background processing"
        ],
        "status": "healthy",
        "redis_connected": realtime_manager.redis_client is not None,
        "active_transformations": len(realtime_manager.active_transformations)
    }


@app.post("/transform/realtime", response_model=TransformationResponse)
async def start_realtime_transformation(
    request: TransformationRequest,
    background_tasks: BackgroundTasks
):
    """Start a transformation with real-time progress tracking."""
    # Create transformation tracking
    transformation_id = await realtime_manager.create_transformation(
        "sample_image.jpg",  # In real implementation, this would be the uploaded file
        request.transformation_type
    )
    
    # Start background processing
    background_tasks.add_task(
        process_transformation_realtime,
        transformation_id,
        request.transformation_type,
        request.parameters or {}
    )
    
    return TransformationResponse(
        transformation_id=transformation_id,
        status="pending",
        message="Transformation started",
        progress=0
    )


@app.get("/transform/{transformation_id}/progress")
async def get_transformation_progress(transformation_id: str):
    """Get current progress of a transformation."""
    if transformation_id not in realtime_manager.active_transformations:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    transformation = realtime_manager.active_transformations[transformation_id]
    return asdict(transformation)


@app.get("/transform/{transformation_id}/stream")
async def stream_transformation_progress(transformation_id: str):
    """Stream real-time progress updates using Server-Sent Events."""
    if transformation_id not in realtime_manager.active_transformations:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    async def event_generator():
        """Generate SSE events for transformation progress."""
        while transformation_id in realtime_manager.active_transformations:
            transformation = realtime_manager.active_transformations[transformation_id]
            
            # Send SSE event
            event_data = {
                "id": transformation.id,
                "status": transformation.status.value,
                "progress": transformation.progress,
                "message": transformation.message,
                "current_step": transformation.current_step,
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            
            # Check if completed
            if transformation.status in [TransformationStatus.COMPLETED, TransformationStatus.FAILED]:
                break
            
            await asyncio.sleep(1)  # Update every second
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@app.websocket("/ws/transformations")
async def websocket_transformations(websocket: WebSocket):
    """WebSocket endpoint for real-time transformation updates."""
    await websocket.accept()
    realtime_manager.websocket_connections.append(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to real-time transformation updates",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        if websocket in realtime_manager.websocket_connections:
            realtime_manager.websocket_connections.remove(websocket)


@app.get("/transformations/active")
async def get_active_transformations():
    """Get all active transformations."""
    return {
        "active_count": len(realtime_manager.active_transformations),
        "transformations": [
            asdict(transformation) 
            for transformation in realtime_manager.active_transformations.values()
        ]
    }


async def process_transformation_realtime(
    transformation_id: str,
    transformation_type: str,
    parameters: Dict[str, Any]
):
    """Background task to process transformation with real-time updates."""
    try:
        # Step 1: Initialization
        await realtime_manager.update_progress(
            transformation_id, 10, "Initializing transformation", "Initialization"
        )
        await asyncio.sleep(1)
        
        # Step 2: Loading image
        await realtime_manager.update_progress(
            transformation_id, 30, "Loading image", "Loading"
        )
        await asyncio.sleep(1)
        
        # Step 3: Processing
        await realtime_manager.update_progress(
            transformation_id, 60, f"Applying {transformation_type}", "Processing"
        )
        await asyncio.sleep(2)
        
        # Step 4: Saving
        await realtime_manager.update_progress(
            transformation_id, 90, "Saving transformed image", "Saving"
        )
        await asyncio.sleep(1)
        
        # Step 5: Complete
        await realtime_manager.update_progress(
            transformation_id, 100, "Transformation completed successfully", "Completed"
        )
        
        # Mark as completed
        await realtime_manager.complete_transformation(transformation_id, success=True)
        
    except Exception as e:
        await realtime_manager.update_progress(
            transformation_id, 0, f"Error: {str(e)}", "Error"
        )
        await realtime_manager.complete_transformation(transformation_id, success=False)


if __name__ == "__main__":
    print("🚀 Starting Stage 6: Real-Time Image Processing API")
    print("Features:")
    print("  - Server-Sent Events (SSE) for real-time progress")
    print("  - WebSocket connections for live updates")
    print("  - Redis pub/sub integration")
    print("  - Background processing with progress tracking")
    print("  - Real-time notifications")
    print("\nEndpoints:")
    print("  - GET / - Health check")
    print("  - POST /transform/realtime - Start real-time transformation")
    print("  - GET /transform/{id}/progress - Get progress")
    print("  - GET /transform/{id}/stream - SSE stream")
    print("  - WS /ws/transformations - WebSocket connection")
    print("  - GET /transformations/active - Active transformations")
    
    uvicorn.run(
        "stage6_realtime_features:app",
        host="0.0.0.0",
        port=8002,  # Different port to avoid conflicts
        reload=True
    ) 