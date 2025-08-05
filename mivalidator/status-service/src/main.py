import sys
import os
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add shared package to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared.utils.redis_client import RedisClient
from shared.utils.logger import setup_logger
from .utils.config import Config

# Setup logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="DICOM Validator Status Service", version="1.0.0")

# Initialize Redis client
redis_client = RedisClient()

# Load configuration
config = Config()

class StatusUpdate(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None

class StatusResponse(BaseModel):
    study_id: str
    status: str
    timestamp: str
    details: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Status service starting up...")
    logger.info("Status service started successfully")

@app.post("/status/{study_id}")
async def update_status(study_id: str, status_update: StatusUpdate):
    """Update the status of a study"""
    try:
        success = redis_client.set_status(study_id, status_update.status, status_update.details)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update status")
        
        return {"message": "Status updated successfully", "study_id": study_id}
        
    except Exception as e:
        logger.error(f"Error updating status for study {study_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/status/{study_id}", response_model=StatusResponse)
async def get_status(study_id: str):
    """Get the status of a study"""
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
    return {"status": "healthy", "service": "status-service"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DICOM Validator Status Service",
        "version": "1.0.0",
        "endpoints": {
            "update_status": "POST /status/{study_id}",
            "get_status": "GET /status/{study_id}",
            "health": "/health"
        }
    } 