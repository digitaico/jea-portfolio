import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .utils.redis_client import RedisClient
from .utils.logger import setup_logger
from .utils.config import Config

# Setup logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="DICOM Validator API Gateway", version="1.0.0")

# Initialize Redis client
redis_client = RedisClient()

# Load configuration
config = Config()

class StatusResponse(BaseModel):
    study_id: str
    status: str
    timestamp: str
    details: dict

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("API Gateway starting up...")
    
    # Ensure uploads directory exists
    uploads_dir = Path(config.uploads_path)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Uploads directory: {uploads_dir}")
    logger.info("API Gateway started successfully")

@app.post("/upload", response_model=dict)
async def upload_dicom(file: UploadFile = File(...)):
    """Upload a DICOM file for processing"""
    try:
        # Validate file
        if not file.filename.lower().endswith(('.dcm', '.dicom')):
            raise HTTPException(status_code=400, detail="Invalid file type. Only DICOM files are allowed.")
        
        if file.size and file.size > config.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Generate study ID
        study_id = str(uuid.uuid4())
        
        # Save file to uploads directory
        uploads_dir = Path(config.uploads_path)
        file_path = uploads_dir / f"{study_id}.dcm"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved DICOM file: {file_path}")
        
        # Publish study.uploaded event
        event_data = {
            "study_id": study_id,
            "file_path": str(file_path),
            "original_filename": file.filename,
            "file_size": file.size or 0
        }
        
        redis_client.publish("uploads", event_data)
        
        # Set initial status
        redis_client.set_status(study_id, "uploaded", {"filename": file.filename})
        
        logger.info(f"Published study.uploaded event for study_id: {study_id}")
        
        return {
            "study_id": study_id,
            "status": "accepted",
            "message": "DICOM file uploaded successfully and queued for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/status/{study_id}", response_model=StatusResponse)
async def get_status(study_id: str):
    """Get the processing status of a study"""
    try:
        status_data = redis_client.get_status(study_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="Study not found")
        
        return StatusResponse(
            study_id=study_id,
            status=status_data["status"],
            timestamp=status_data["timestamp"],
            details=status_data["details"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for study {study_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DICOM Validator API Gateway",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "status": "/status/{study_id}",
            "health": "/health"
        }
    } 