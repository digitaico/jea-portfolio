"""
FastAPI application for image processing service.
Provides REST API endpoints for image transformations with database integration.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import os
import uuid
from pathlib import Path

from image_transformer import ImageColorTransformer
from database import db_manager, TransformationHistory, DatabaseManager
from config import settings, ensure_directories

# Ensure directories exist
ensure_directories()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Image processing API with transformation capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class TransformationRequest(BaseModel):
    transformation_type: str
    parameters: Optional[Dict[str, Any]] = {}
    output_format: Optional[str] = "jpg"


class TransformationResponse(BaseModel):
    id: int
    image_path: str
    transformation_type: str
    output_path: str
    processing_time: Optional[int]
    created_at: str


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


# Dependency for database session
def get_db():
    return db_manager


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        database="connected" if db_manager.engine else "disconnected",
        version="1.0.0"
    )


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected" if db_manager.engine else "disconnected",
        "timestamp": time.time()
    }


@app.post("/transform/upload", response_model=TransformationResponse)
async def transform_upload(
    file: UploadFile = File(...),
    transformation_type: str = Query(..., description="Type of transformation to apply"),
    parameters: Optional[str] = Query(None, description="JSON string of parameters"),
    db: DatabaseManager = Depends(get_db)
):
    """
    Upload and transform an image.
    
    Supported transformation types:
    - brightness, contrast, sepia, grayscale, invert
    - gaussian_blur, median_filter, unsharp_mask
    - emboss, find_edges, contour
    - rotate, resize
    """
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        if file.size > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix or '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        upload_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Save uploaded file
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse parameters
        params = {}
        if parameters:
            try:
                import json
                params = json.loads(parameters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid parameters JSON")
        
        # Process image
        start_time = time.time()
        transformer = ImageColorTransformer(upload_path)
        
        # Apply transformation
        if transformation_type == "brightness":
            factor = params.get("factor", 1.3)
            transformer.adjust_brightness(factor)
        elif transformation_type == "contrast":
            factor = params.get("factor", 1.5)
            transformer.adjust_contrast(factor)
        elif transformation_type == "sepia":
            transformer.apply_sepia()
        elif transformation_type == "grayscale":
            transformer.to_grayscale()
        elif transformation_type == "invert":
            transformer.invert_colors()
        elif transformation_type == "gaussian_blur":
            kernel_size = params.get("kernel_size", 5)
            transformer.apply_gaussian_blur(kernel_size)
        elif transformation_type == "gaussian_blur_pillow":
            radius = params.get("radius", 2.0)
            transformer.apply_gaussian_blur_pillow(radius)
        elif transformation_type == "unsharp_mask":
            radius = params.get("radius", 2.0)
            percent = params.get("percent", 150)
            threshold = params.get("threshold", 3)
            transformer.apply_unsharp_mask_pillow(radius, percent, threshold)
        elif transformation_type == "emboss":
            transformer.apply_emboss_pillow()
        elif transformation_type == "find_edges":
            transformer.apply_find_edges_pillow()
        elif transformation_type == "contour":
            transformer.apply_contour_pillow()
        elif transformation_type == "rotate":
            angle = params.get("angle", 45)
            expand = params.get("expand", True)
            transformer.rotate_pillow(angle, expand)
        elif transformation_type == "resize":
            width = params.get("width", 800)
            height = params.get("height", 600)
            resample = params.get("resample", "lanczos")
            transformer.resize_pillow(width, height, resample)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported transformation type: {transformation_type}")
        
        # Save transformed image
        output_filename = f"transformed_{uuid.uuid4()}.jpg"
        output_path = os.path.join(settings.output_dir, output_filename)
        transformer.save_image(output_path)
        
        processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        # Save to database
        transformation = db.save_transformation(
            image_path=upload_path,
            transformation_type=transformation_type,
            parameters=params,
            output_path=output_path,
            processing_time=processing_time
        )
        
        if not transformation:
            raise HTTPException(status_code=500, detail="Failed to save transformation to database")
        
        return TransformationResponse(
            id=transformation.id,
            image_path=upload_path,
            transformation_type=transformation_type,
            output_path=output_path,
            processing_time=processing_time,
            created_at=transformation.created_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/transformations", response_model=List[TransformationResponse])
async def get_transformations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    transformation_type: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db)
):
    """Get transformation history."""
    transformations = db.get_transformation_history(limit=limit, offset=offset, transformation_type=transformation_type)
    
    return [
        TransformationResponse(
            id=t.id,
            image_path=t.image_path,
            transformation_type=t.transformation_type,
            output_path=t.output_path or "",
            processing_time=t.processing_time,
            created_at=t.created_at.isoformat()
        )
        for t in transformations
    ]


@app.get("/transformations/{transformation_id}", response_model=TransformationResponse)
async def get_transformation(
    transformation_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """Get specific transformation by ID."""
    transformation = db.get_transformation_by_id(transformation_id)
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    return TransformationResponse(
        id=transformation.id,
        image_path=transformation.image_path,
        transformation_type=transformation.transformation_type,
        output_path=transformation.output_path or "",
        processing_time=transformation.processing_time,
        created_at=transformation.created_at.isoformat()
    )


@app.get("/download/{transformation_id}")
async def download_transformation(
    transformation_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """Download transformed image."""
    transformation = db.get_transformation_by_id(transformation_id)
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    if not transformation.output_path or not os.path.exists(transformation.output_path):
        raise HTTPException(status_code=404, detail="Transformed image not found")
    
    return FileResponse(
        transformation.output_path,
        media_type="image/jpeg",
        filename=f"transformed_{transformation_id}.jpg"
    )


@app.delete("/transformations/{transformation_id}")
async def delete_transformation(
    transformation_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """Delete transformation and associated files."""
    transformation = db.get_transformation_by_id(transformation_id)
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    # Delete files
    if transformation.image_path and os.path.exists(transformation.image_path):
        os.remove(transformation.image_path)
    
    if transformation.output_path and os.path.exists(transformation.output_path):
        os.remove(transformation.output_path)
    
    # Delete from database
    success = db.delete_transformation(transformation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete transformation")
    
    return {"message": "Transformation deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 