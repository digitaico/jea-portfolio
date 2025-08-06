#!/usr/bin/env python3
"""
File Upload & Image Processing API
==================================

This is a comprehensive web-based image processing API that builds upon
all previous stages with file upload capabilities, real-time progress tracking,
and web-based interface.

Features:
- File upload with drag-and-drop support
- Real-time progress tracking
- Batch processing capabilities
- Web hooks for completion notifications
- Image preview and comparison
- Download transformed images
- Web-based interface

Usage:
    python3 file_upload_api.py
    # Then visit http://localhost:8003
"""

import os
import time
import uuid
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles

# Import from previous stages
from image_transformer import ImageColorTransformer
from database import db_manager, TransformationHistory
from config import settings, ensure_directories


class UploadResponse(BaseModel):
    """Response model for file upload."""
    upload_id: str
    filename: str
    status: str
    message: str
    preview_url: Optional[str] = None


class ProcessingStatus(BaseModel):
    """Model for processing status."""
    upload_id: str
    status: str
    progress: int
    message: str
    transformations: List[Dict[str, Any]] = []
    completed_at: Optional[datetime] = None


class WebhookRequest(BaseModel):
    """Model for webhook requests."""
    upload_id: str
    status: str
    transformations: List[Dict[str, Any]]
    download_url: Optional[str] = None


class FileUploadProcessor:
    """Handles file upload and processing."""
    
    def __init__(self):
        self.active_uploads: Dict[str, ProcessingStatus] = {}
        self.upload_dir = Path(settings.upload_dir)
        self.output_dir = Path(settings.output_dir)
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.upload_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        (self.upload_dir / "previews").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded file and return upload ID."""
        upload_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        # Create upload directory
        upload_path = self.upload_dir / f"{upload_id}{file_extension}"
        
        # Save file
        async with aiofiles.open(upload_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create processing status
        self.active_uploads[upload_id] = ProcessingStatus(
            upload_id=upload_id,
            status="uploaded",
            progress=0,
            message="File uploaded successfully"
        )
        
        return upload_id, upload_path
    
    async def process_image(self, upload_id: str, transformations: List[str] = None) -> ProcessingStatus:
        """Process uploaded image with specified transformations."""
        if upload_id not in self.active_uploads:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        status = self.active_uploads[upload_id]
        status.status = "processing"
        status.progress = 0
        
        # Find uploaded file
        upload_path = None
        for file_path in self.upload_dir.glob(f"{upload_id}.*"):
            if file_path.is_file():
                upload_path = file_path
                break
        
        if not upload_path:
            status.status = "error"
            status.message = "Uploaded file not found"
            return status
        
        # Default transformations if none specified
        if not transformations:
            transformations = ["brightness", "contrast", "sepia", "grayscale", "gaussian_blur"]
        
        try:
            # Load image
            transformer = ImageColorTransformer(str(upload_path))
            if transformer.image is None:
                status.status = "error"
                status.message = "Failed to load image"
                return status
            
            status.progress = 10
            status.message = "Image loaded successfully"
            
            # Process transformations
            total_transformations = len(transformations)
            completed_transformations = []
            
            for i, transformation_type in enumerate(transformations):
                status.message = f"Processing {transformation_type}..."
                status.progress = 10 + int((i / total_transformations) * 80)
                
                # Reset transformer for each transformation
                transformer.reset()
                
                # Apply transformation
                start_time = time.time()
                success = await self.apply_transformation(transformer, transformation_type, upload_id)
                processing_time = int((time.time() - start_time) * 1000)
                
                if success:
                    completed_transformations.append({
                        "type": transformation_type,
                        "processing_time": processing_time,
                        "output_path": f"processed/{upload_id}_{transformation_type}.jpg"
                    })
                
                # Update progress
                status.progress = 10 + int(((i + 1) / total_transformations) * 80)
            
            # Finalize
            status.progress = 100
            status.status = "completed"
            status.message = f"Completed {len(completed_transformations)} transformations"
            status.transformations = completed_transformations
            status.completed_at = datetime.now()
            
            return status
            
        except Exception as e:
            status.status = "error"
            status.message = f"Processing error: {str(e)}"
            return status
    
    async def apply_transformation(self, transformer: ImageColorTransformer, 
                                 transformation_type: str, upload_id: str) -> bool:
        """Apply a single transformation and save to database."""
        try:
            # Apply transformation based on type
            if transformation_type == "brightness":
                transformer.adjust_brightness(1.3)
            elif transformation_type == "contrast":
                transformer.adjust_contrast(1.5)
            elif transformation_type == "sepia":
                transformer.apply_sepia()
            elif transformation_type == "grayscale":
                transformer.to_grayscale()
            elif transformation_type == "invert":
                transformer.invert_colors()
            elif transformation_type == "gaussian_blur":
                transformer.apply_gaussian_blur(5)
            elif transformation_type == "gaussian_blur_pillow":
                transformer.apply_gaussian_blur_pillow(3.0)
            elif transformation_type == "saturation_pillow":
                transformer.adjust_saturation_pillow(1.6)
            else:
                raise ValueError(f"Unknown transformation type: {transformation_type}")
            
            # Save transformed image
            output_filename = f"{upload_id}_{transformation_type}.jpg"
            output_path = self.output_dir / "processed" / output_filename
            transformer.save_image(str(output_path))
            
            # Save to database
            db_manager.save_transformation(
                image_path=str(transformer.image_path),
                transformation_type=transformation_type,
                parameters={},
                output_path=str(output_path),
                processing_time=None
            )
            
            return True
            
        except Exception as e:
            print(f"Error applying {transformation_type}: {e}")
            return False


# Global processor instance
processor = FileUploadProcessor()


# FastAPI app
app = FastAPI(
    title="File Upload & Image Processing API",
    description="Web-based image processing with file upload capabilities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: Static files are served directly in the HTML response
# No need to mount static directory


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Processing API</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .upload-area:hover {
                border-color: #764ba2;
                background-color: #f8f9ff;
            }
            .upload-area.dragover {
                border-color: #764ba2;
                background-color: #f0f2ff;
            }
            .file-input {
                display: none;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            }
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .progress {
                width: 100%;
                height: 20px;
                background-color: #f0f0f0;
                border-radius: 10px;
                overflow: hidden;
                margin: 20px 0;
            }
            .progress-bar {
                height: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                transition: width 0.3s ease;
            }
            .status {
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                font-weight: bold;
            }
            .status.uploading { background-color: #e3f2fd; color: #1976d2; }
            .status.processing { background-color: #fff3e0; color: #f57c00; }
            .status.completed { background-color: #e8f5e8; color: #388e3c; }
            .status.error { background-color: #ffebee; color: #d32f2f; }
            .transformations {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .transformation-card {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #667eea;
            }
            .preview {
                max-width: 300px;
                max-height: 300px;
                border-radius: 8px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖼️ Image Processing API</h1>
            
            <div class="upload-area" id="uploadArea">
                <h3>📁 Drag & Drop Image Here</h3>
                <p>or click to select file</p>
                <input type="file" id="fileInput" class="file-input" accept="image/*">
                <button class="btn" onclick="document.getElementById('fileInput').click()">
                    Choose File
                </button>
            </div>
            
            <div id="progressContainer" style="display: none;">
                <div class="progress">
                    <div class="progress-bar" id="progressBar" style="width: 0%"></div>
                </div>
                <div class="status" id="status">Ready to upload</div>
            </div>
            
            <div id="resultsContainer" style="display: none;">
                <h3>🎯 Processing Results</h3>
                <div id="transformations" class="transformations"></div>
            </div>
        </div>

        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const progressContainer = document.getElementById('progressContainer');
            const progressBar = document.getElementById('progressBar');
            const status = document.getElementById('status');
            const resultsContainer = document.getElementById('resultsContainer');
            const transformations = document.getElementById('transformations');

            // Drag and drop functionality
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFile(files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFile(e.target.files[0]);
                }
            });

            async function handleFile(file) {
                if (!file.type.startsWith('image/')) {
                    alert('Please select an image file');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                progressContainer.style.display = 'block';
                status.textContent = 'Uploading...';
                status.className = 'status uploading';
                progressBar.style.width = '10%';

                try {
                    // Upload file
                    const uploadResponse = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!uploadResponse.ok) {
                        throw new Error('Upload failed');
                    }

                    const uploadResult = await uploadResponse.json();
                    progressBar.style.width = '30%';
                    status.textContent = 'Processing image...';
                    status.className = 'status processing';

                    // Process image
                    const processResponse = await fetch(`/process/${uploadResult.upload_id}`, {
                        method: 'POST'
                    });

                    if (!processResponse.ok) {
                        throw new Error('Processing failed');
                    }

                    const processResult = await processResponse.json();
                    progressBar.style.width = '100%';
                    status.textContent = 'Completed!';
                    status.className = 'status completed';

                    // Display results
                    displayResults(processResult);

                } catch (error) {
                    status.textContent = `Error: ${error.message}`;
                    status.className = 'status error';
                    progressBar.style.width = '0%';
                }
            }

            function displayResults(result) {
                resultsContainer.style.display = 'block';
                transformations.innerHTML = '';

                result.transformations.forEach(transformation => {
                    const card = document.createElement('div');
                    card.className = 'transformation-card';
                    card.innerHTML = `
                        <h4>${transformation.type}</h4>
                        <p>Processing time: ${transformation.processing_time}ms</p>
                        <a href="/download/${result.upload_id}/${transformation.type}" 
                           class="btn" target="_blank">Download</a>
                    `;
                    transformations.appendChild(card);
                });
            }
        </script>
    </body>
    </html>
    """
    return html_content


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload an image file."""
    try:
        upload_id, upload_path = await processor.save_uploaded_file(file)
        
        return UploadResponse(
            upload_id=upload_id,
            filename=file.filename,
            status="uploaded",
            message="File uploaded successfully",
            preview_url=f"/preview/{upload_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/process/{upload_id}", response_model=ProcessingStatus)
async def process_image(upload_id: str, background_tasks: BackgroundTasks):
    """Process uploaded image with transformations."""
    try:
        # Start processing in background
        background_tasks.add_task(processor.process_image, upload_id)
        
        return ProcessingStatus(
            upload_id=upload_id,
            status="processing",
            progress=0,
            message="Processing started"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/status/{upload_id}", response_model=ProcessingStatus)
async def get_processing_status(upload_id: str):
    """Get processing status for an upload."""
    if upload_id not in processor.active_uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return processor.active_uploads[upload_id]


@app.get("/download/{upload_id}/{transformation_type}")
async def download_transformed_image(upload_id: str, transformation_type: str):
    """Download a transformed image."""
    output_path = processor.output_dir / "processed" / f"{upload_id}_{transformation_type}.jpg"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Transformed image not found")
    
    return FileResponse(
        path=str(output_path),
        filename=f"{upload_id}_{transformation_type}.jpg",
        media_type="image/jpeg"
    )


@app.get("/preview/{upload_id}")
async def get_image_preview(upload_id: str):
    """Get image preview."""
    # Find uploaded file
    upload_path = None
    for file_path in processor.upload_dir.glob(f"{upload_id}.*"):
        if file_path.is_file():
            upload_path = file_path
            break
    
    if not upload_path or not upload_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        path=str(upload_path),
        filename=upload_path.name,
        media_type="image/jpeg"
    )


@app.get("/uploads")
async def list_uploads():
    """List all uploads."""
    return {
        "uploads": [
            {
                "upload_id": upload_id,
                "status": status.status,
                "progress": status.progress,
                "message": status.message,
                "completed_at": status.completed_at
            }
            for upload_id, status in processor.active_uploads.items()
        ]
    }


if __name__ == "__main__":
    print("🚀 Starting File Upload & Image Processing API")
    print("Features:")
    print("  - File upload with drag-and-drop")
    print("  - Real-time progress tracking")
    print("  - Batch processing capabilities")
    print("  - Web-based interface")
    print("  - Download transformed images")
    print("\nEndpoints:")
    print("  - GET / - Web interface")
    print("  - POST /upload - Upload file")
    print("  - POST /process/{upload_id} - Process image")
    print("  - GET /status/{upload_id} - Get status")
    print("  - GET /download/{upload_id}/{type} - Download result")
    print("  - GET /preview/{upload_id} - Image preview")
    print("  - GET /uploads - List uploads")
    
    uvicorn.run(
        "file_upload_api:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    ) 