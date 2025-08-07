#!/usr/bin/env python3
"""
Image Processing Service for microservices architecture.

This service handles image uploads, processing, transformations,
and storage using the existing image transformer functionality.
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import aiofiles

from shared.models import (
    ImageUpload, ImageProcessing, Event, EventType, EventStatus,
    APIResponse, ServiceHealth
)
from shared.utils import Logger, EventBus, ServiceHealth as HealthMonitor


# Initialize logger
logger = Logger("image-service", os.getenv("LOG_LEVEL", "INFO"))

# Initialize event bus
event_bus = EventBus(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Service configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory storage (in production, use a database)
uploads = {}
processings = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Image Processing Service")
    yield
    logger.info("Shutting down Image Processing Service")


# Create FastAPI app
app = FastAPI(
    title="Image Processing Service",
    description="Service for image uploads and processing",
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


def validate_file_extension(filename: str) -> bool:
    """Validate file extension."""
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """Validate file size."""
    return file_size <= MAX_FILE_SIZE


async def save_upload_file(upload_file: UploadFile, upload_id: str) -> str:
    """Save uploaded file."""
    file_path = os.path.join(UPLOAD_DIR, f"{upload_id}_{upload_file.filename}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await upload_file.read()
        await f.write(content)
    
    return file_path


async def process_image_background(upload_id: str, transformation_type: str, 
                                 parameters: Dict[str, Any], user_id: str):
    """Background task for image processing."""
    try:
        # Get upload
        upload = uploads.get(upload_id)
        if not upload:
            logger.error(f"Upload not found: {upload_id}")
            return
        
        # Create processing record
        processing_id = str(uuid.uuid4())
        processing = ImageProcessing(
            id=processing_id,
            upload_id=upload_id,
            user_id=user_id,
            transformation_type=transformation_type,
            parameters=parameters,
            status="processing",
            progress=0,
            created_at=datetime.utcnow()
        )
        processings[processing_id] = processing
        
        # Publish processing started event
        await event_bus.publish_event(
            EventType.IMAGE_PROCESSING_STARTED,
            {
                "processing_id": processing_id,
                "upload_id": upload_id,
                "user_id": user_id,
                "transformation_type": transformation_type
            },
            user_id=user_id
        )
        
        # Simulate processing steps
        for progress in range(0, 101, 10):
            processing.progress = progress
            await asyncio.sleep(0.5)  # Simulate processing time
        
        # Generate output filename
        output_filename = f"{upload_id}_{transformation_type}.jpg"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # In a real implementation, you would use the image transformer here
        # For now, we'll just copy the original file
        async with aiofiles.open(upload["file_path"], 'rb') as src:
            content = await src.read()
            async with aiofiles.open(output_path, 'wb') as dst:
                await dst.write(content)
        
        # Update processing record
        processing.status = "completed"
        processing.progress = 100
        processing.output_path = output_path
        processing.completed_at = datetime.utcnow()
        processing.processing_time = 5000  # 5 seconds
        
        # Publish processing completed event
        await event_bus.publish_event(
            EventType.IMAGE_PROCESSING_COMPLETED,
            {
                "processing_id": processing_id,
                "upload_id": upload_id,
                "user_id": user_id,
                "transformation_type": transformation_type,
                "output_path": output_path
            },
            user_id=user_id
        )
        
        logger.info(f"Image processing completed: {processing_id}")
        
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        
        # Update processing record
        if processing_id in processings:
            processings[processing_id].status = "failed"
            processings[processing_id].error_message = str(e)
            processings[processing_id].completed_at = datetime.utcnow()
        
        # Publish processing failed event
        await event_bus.publish_event(
            EventType.IMAGE_PROCESSING_FAILED,
            {
                "processing_id": processing_id,
                "upload_id": upload_id,
                "user_id": user_id,
                "transformation_type": transformation_type,
                "error": str(e)
            },
            user_id=user_id
        )


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint."""
    return APIResponse(
        success=True,
        message="Image Processing Service is running",
        data={
            "service": "image-service",
            "version": "1.0.0",
            "status": "healthy"
        }
    )


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Health check endpoint."""
    health = HealthMonitor("image-service", "1.0.0")
    return health.get_health()


@app.post("/upload")
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """Upload an image."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file size
        content = await file.read()
        file_size = len(content)
        
        if not validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate upload ID
        upload_id = str(uuid.uuid4())
        
        # Save file
        file_path = await save_upload_file(file, upload_id)
        
        # Create upload record
        upload = ImageUpload(
            id=upload_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            created_at=datetime.utcnow(),
            status="uploaded"
        )
        
        uploads[upload_id] = upload.dict()
        
        # Publish upload event
        await event_bus.publish_event(
            EventType.IMAGE_UPLOADED,
            {
                "upload_id": upload_id,
                "user_id": user_id,
                "filename": file.filename,
                "file_size": file_size
            },
            user_id=user_id
        )
        
        logger.info(f"Image uploaded: {upload_id} by user {user_id}")
        
        return APIResponse(
            success=True,
            message="Image uploaded successfully",
            data=upload.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@app.post("/process/{upload_id}")
async def process_image(
    upload_id: str,
    background_tasks: BackgroundTasks,
    transformation_type: str = Form(...),
    parameters: str = Form("{}"),
    user_id: str = Form(...)
):
    """Process an uploaded image."""
    try:
        # Check if upload exists
        if upload_id not in uploads:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        upload = uploads[upload_id]
        
        # Check if user owns the upload
        if upload["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Parse parameters
        try:
            import json
            params = json.loads(parameters)
        except json.JSONDecodeError:
            params = {}
        
        # Start background processing
        background_tasks.add_task(
            process_image_background,
            upload_id,
            transformation_type,
            params,
            user_id
        )
        
        logger.info(f"Image processing started: {upload_id} -> {transformation_type}")
        
        return APIResponse(
            success=True,
            message="Image processing started",
            data={
                "upload_id": upload_id,
                "transformation_type": transformation_type,
                "status": "processing"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")


@app.get("/status/{upload_id}")
async def get_processing_status(upload_id: str, user_id: str):
    """Get processing status for an upload."""
    try:
        # Check if upload exists
        if upload_id not in uploads:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        upload = uploads[upload_id]
        
        # Check if user owns the upload
        if upload["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get processing records for this upload
        upload_processings = [
            p for p in processings.values()
            if p["upload_id"] == upload_id
        ]
        
        return APIResponse(
            success=True,
            message="Processing status retrieved",
            data={
                "upload": upload,
                "processings": upload_processings
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


@app.get("/download/{upload_id}/{transformation_type}")
async def download_processed_image(upload_id: str, transformation_type: str, user_id: str):
    """Download a processed image."""
    try:
        # Check if upload exists
        if upload_id not in uploads:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        upload = uploads[upload_id]
        
        # Check if user owns the upload
        if upload["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Find processing record
        processing = None
        for p in processings.values():
            if (p["upload_id"] == upload_id and 
                p["transformation_type"] == transformation_type):
                processing = p
                break
        
        if not processing:
            raise HTTPException(status_code=404, detail="Processing not found")
        
        if processing["status"] != "completed":
            raise HTTPException(status_code=400, detail="Processing not completed")
        
        # Check if output file exists
        output_path = processing["output_path"]
        if not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="Output file not found")
        
        # Return file
        return FileResponse(
            output_path,
            media_type="image/jpeg",
            filename=f"{upload_id}_{transformation_type}.jpg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@app.get("/uploads")
async def list_uploads(user_id: str, limit: int = 10, offset: int = 0):
    """List user's uploads."""
    try:
        # Filter uploads by user
        user_uploads = [
            upload for upload in uploads.values()
            if upload["user_id"] == user_id
        ]
        
        # Sort by creation date (newest first)
        user_uploads.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        total = len(user_uploads)
        paginated_uploads = user_uploads[offset:offset + limit]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_uploads)} uploads",
            data={
                "uploads": paginated_uploads,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"List uploads failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list uploads")


@app.delete("/uploads/{upload_id}")
async def delete_upload(upload_id: str, user_id: str):
    """Delete an upload and its processed images."""
    try:
        # Check if upload exists
        if upload_id not in uploads:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        upload = uploads[upload_id]
        
        # Check if user owns the upload
        if upload["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete file
        if os.path.exists(upload["file_path"]):
            os.remove(upload["file_path"])
        
        # Delete processed images
        for processing in processings.values():
            if (processing["upload_id"] == upload_id and 
                processing["output_path"] and 
                os.path.exists(processing["output_path"])):
                os.remove(processing["output_path"])
        
        # Remove from storage
        del uploads[upload_id]
        
        # Remove processing records
        processings_to_remove = [
            pid for pid, p in processings.items()
            if p["upload_id"] == upload_id
        ]
        for pid in processings_to_remove:
            del processings[pid]
        
        logger.info(f"Upload deleted: {upload_id}")
        
        return APIResponse(
            success=True,
            message="Upload deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail="Delete failed")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
