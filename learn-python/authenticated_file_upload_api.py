#!/usr/bin/env python3
"""
Authenticated File Upload & Image Processing API
================================================

This is the authenticated version of the file upload API with OAuth2 authentication,
role-based access control (RBAC), and social network integration.

Features:
- OAuth2 authentication with JWT tokens
- Social network login (Google, GitHub, Facebook)
- Role-based access control (Admin, User, Premium, Guest)
- User management and sessions
- Secure file upload and processing
- User-specific storage and history

Usage:
    python3 authenticated_file_upload_api.py
    # Then visit http://localhost:8004
"""

import os
import time
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

# Import from previous stages
from image_transformer import ImageColorTransformer
from database import db_manager, TransformationHistory
from config import settings, ensure_directories
from auth_system import (
    AuthManager, User, UserRole, UserStatus, AuthProvider,
    Token, TokenData, OAuth2Request, UserCreate, UserUpdate,
    get_current_user, get_current_active_user, require_role, require_roles
)


class UploadResponse(BaseModel):
    """Response model for file upload."""
    upload_id: str
    filename: str
    status: str
    message: str
    preview_url: Optional[str] = None
    user_id: str


class ProcessingStatus(BaseModel):
    """Model for processing status."""
    upload_id: str
    status: str
    progress: int
    message: str
    transformations: List[Dict[str, Any]] = []
    completed_at: Optional[datetime] = None
    user_id: str


class AuthenticatedFileUploadProcessor:
    """Handles file upload and processing with authentication."""
    
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
        (self.output_dir / "users").mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile, user_id: str) -> tuple[str, Path]:
        """Save uploaded file and return upload ID."""
        upload_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        # Create user-specific upload directory
        user_upload_dir = self.upload_dir / user_id
        user_upload_dir.mkdir(exist_ok=True)
        
        # Create upload directory
        upload_path = user_upload_dir / f"{upload_id}{file_extension}"
        
        # Save file
        async with aiofiles.open(upload_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create processing status
        self.active_uploads[upload_id] = ProcessingStatus(
            upload_id=upload_id,
            status="uploaded",
            progress=0,
            message="File uploaded successfully",
            user_id=user_id
        )
        
        return upload_id, upload_path
    
    async def process_image(self, upload_id: str, user_id: str, transformations: List[str] = None) -> ProcessingStatus:
        """Process uploaded image with specified transformations."""
        if upload_id not in self.active_uploads:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        status_obj = self.active_uploads[upload_id]
        
        # Check if user owns this upload
        if status_obj.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        status_obj.status = "processing"
        status_obj.progress = 0
        
        # Find uploaded file
        user_upload_dir = self.upload_dir / user_id
        upload_path = None
        for file_path in user_upload_dir.glob(f"{upload_id}.*"):
            if file_path.is_file():
                upload_path = file_path
                break
        
        if not upload_path:
            status_obj.status = "error"
            status_obj.message = "Uploaded file not found"
            return status_obj
        
        # Default transformations if none specified
        if not transformations:
            transformations = ["brightness", "contrast", "sepia", "grayscale", "gaussian_blur"]
        
        try:
            # Load image
            transformer = ImageColorTransformer(str(upload_path))
            if transformer.image is None:
                status_obj.status = "error"
                status_obj.message = "Failed to load image"
                return status_obj
            
            status_obj.progress = 10
            status_obj.message = "Image loaded successfully"
            
            # Process transformations
            total_transformations = len(transformations)
            completed_transformations = []
            
            for i, transformation_type in enumerate(transformations):
                status_obj.message = f"Processing {transformation_type}..."
                status_obj.progress = 10 + int((i / total_transformations) * 80)
                
                # Reset transformer for each transformation
                transformer.reset()
                
                # Apply transformation
                start_time = time.time()
                success = await self.apply_transformation(transformer, transformation_type, upload_id, user_id)
                processing_time = int((time.time() - start_time) * 1000)
                
                if success:
                    completed_transformations.append({
                        "type": transformation_type,
                        "processing_time": processing_time,
                        "output_path": f"users/{user_id}/{upload_id}_{transformation_type}.jpg"
                    })
                
                # Update progress
                status_obj.progress = 10 + int(((i + 1) / total_transformations) * 80)
            
            # Finalize
            status_obj.progress = 100
            status_obj.status = "completed"
            status_obj.message = f"Completed {len(completed_transformations)} transformations"
            status_obj.transformations = completed_transformations
            status_obj.completed_at = datetime.now()
            
            return status_obj
            
        except Exception as e:
            status_obj.status = "error"
            status_obj.message = f"Processing error: {str(e)}"
            return status_obj
    
    async def apply_transformation(self, transformer: ImageColorTransformer, 
                                 transformation_type: str, upload_id: str, user_id: str) -> bool:
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
            
            # Save transformed image to user-specific directory
            user_output_dir = self.output_dir / "users" / user_id
            user_output_dir.mkdir(exist_ok=True)
            
            output_filename = f"{upload_id}_{transformation_type}.jpg"
            output_path = user_output_dir / output_filename
            transformer.save_image(str(output_path))
            
            # Save to database with user information
            db_manager.save_transformation(
                image_path=str(transformer.image_path),
                transformation_type=transformation_type,
                parameters={"user_id": user_id},
                output_path=str(output_path),
                processing_time=None
            )
            
            return True
            
        except Exception as e:
            print(f"Error applying {transformation_type}: {e}")
            return False


# Global processor instance
processor = AuthenticatedFileUploadProcessor()


# FastAPI app
app = FastAPI(
    title="Authenticated File Upload & Image Processing API",
    description="Web-based image processing with OAuth2 authentication and RBAC",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface with authentication."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Authenticated Image Processing API</title>
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
            .auth-section {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .login-form {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            .login-form input {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                flex: 1;
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
            .btn-secondary {
                background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
            }
            .btn-success {
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            }
            .social-login {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                transition: all 0.3s ease;
                cursor: pointer;
                display: none;
            }
            .upload-area.authenticated {
                display: block;
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
            .user-info {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .hidden {
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Authenticated Image Processing API</h1>
            
            <!-- Authentication Section -->
            <div class="auth-section" id="authSection">
                <h3>🔑 Authentication</h3>
                
                <!-- Login Form -->
                <div class="login-form">
                    <input type="email" id="email" placeholder="Email" value="user@example.com">
                    <input type="password" id="password" placeholder="Password" value="user123">
                    <button class="btn" onclick="login()">Login</button>
                </div>
                
                <!-- Social Login -->
                <div class="social-login">
                    <button class="btn btn-secondary" onclick="socialLogin('google')">Google</button>
                    <button class="btn btn-secondary" onclick="socialLogin('github')">GitHub</button>
                    <button class="btn btn-secondary" onclick="socialLogin('facebook')">Facebook</button>
                </div>
                
                <!-- Mock Tokens -->
                <div style="margin-top: 20px;">
                    <h4>Mock Tokens for Testing:</h4>
                    <p><strong>Admin:</strong> admin@example.com / admin123</p>
                    <p><strong>User:</strong> user@example.com / user123</p>
                    <p><strong>Premium:</strong> premium@example.com / premium123</p>
                </div>
            </div>
            
            <!-- User Info -->
            <div class="user-info hidden" id="userInfo">
                <h3>👤 User Information</h3>
                <p><strong>Email:</strong> <span id="userEmail"></span></p>
                <p><strong>Role:</strong> <span id="userRole"></span></p>
                <p><strong>Status:</strong> <span id="userStatus"></span></p>
                <button class="btn btn-secondary" onclick="logout()">Logout</button>
            </div>
            
            <!-- Upload Section -->
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
            let currentUser = null;
            let accessToken = null;
            
            const authSection = document.getElementById('authSection');
            const userInfo = document.getElementById('userInfo');
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const progressContainer = document.getElementById('progressContainer');
            const progressBar = document.getElementById('progressBar');
            const status = document.getElementById('status');
            const resultsContainer = document.getElementById('resultsContainer');
            const transformations = document.getElementById('transformations');

            async function login() {
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                try {
                    const formData = new FormData();
                    formData.append('username', email);
                    formData.append('password', password);
                    
                    const response = await fetch('/token', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        accessToken = result.access_token;
                        currentUser = result.user;
                        showAuthenticatedUser();
                    } else {
                        alert('Login failed. Please check your credentials.');
                    }
                } catch (error) {
                    alert('Login error: ' + error.message);
                }
            }
            
            async function socialLogin(provider) {
                try {
                    // Mock social login
                    const mockCodes = {
                        'google': 'mock_google_code_123',
                        'github': 'mock_github_code_456',
                        'facebook': 'mock_facebook_code_789'
                    };
                    
                    const response = await fetch('/oauth2/token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            provider: provider,
                            code: mockCodes[provider],
                            redirect_uri: 'http://localhost:8004'
                        })
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        accessToken = result.access_token;
                        currentUser = result.user;
                        showAuthenticatedUser();
                    } else {
                        alert('Social login failed.');
                    }
                } catch (error) {
                    alert('Social login error: ' + error.message);
                }
            }
            
            function showAuthenticatedUser() {
                authSection.classList.add('hidden');
                userInfo.classList.remove('hidden');
                uploadArea.classList.add('authenticated');
                
                document.getElementById('userEmail').textContent = currentUser.email;
                document.getElementById('userRole').textContent = currentUser.role;
                document.getElementById('userStatus').textContent = currentUser.status;
            }
            
            function logout() {
                currentUser = null;
                accessToken = null;
                authSection.classList.remove('hidden');
                userInfo.classList.add('hidden');
                uploadArea.classList.remove('authenticated');
                resultsContainer.style.display = 'none';
                progressContainer.style.display = 'none';
            }

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
                if (!currentUser || !accessToken) {
                    alert('Please login first');
                    return;
                }
                
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
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        },
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
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        }
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


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint for OAuth2 password flow."""
    user = auth_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    return Token(
        access_token=access_token,
        expires_in=auth_manager.access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        user=user
    )


@app.post("/oauth2/token", response_model=Token)
async def oauth2_token(request: OAuth2Request):
    """OAuth2 token endpoint for social login."""
    # Exchange code for token
    token = auth_manager.social_provider.exchange_code_for_token(request.provider, request.code)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    # Authenticate user with social token
    user = auth_manager.authenticate_social_user(request.provider, token)
    if not user:
        raise HTTPException(status_code=400, detail="Failed to authenticate user")
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    return Token(
        access_token=access_token,
        expires_in=auth_manager.access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        user=user
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload an image file (authenticated)."""
    try:
        upload_id, upload_path = await processor.save_uploaded_file(file, current_user.id)
        
        return UploadResponse(
            upload_id=upload_id,
            filename=file.filename,
            status="uploaded",
            message="File uploaded successfully",
            preview_url=f"/preview/{upload_id}",
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/process/{upload_id}", response_model=ProcessingStatus)
async def process_image(
    upload_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Process uploaded image with transformations (authenticated)."""
    try:
        # Start processing in background
        background_tasks.add_task(processor.process_image, upload_id, current_user.id)
        
        return ProcessingStatus(
            upload_id=upload_id,
            status="processing",
            progress=0,
            message="Processing started",
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/status/{upload_id}", response_model=ProcessingStatus)
async def get_processing_status(
    upload_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get processing status for an upload (authenticated)."""
    if upload_id not in processor.active_uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    status_obj = processor.active_uploads[upload_id]
    
    # Check if user owns this upload
    if status_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return status_obj


@app.get("/download/{upload_id}/{transformation_type}")
async def download_transformed_image(
    upload_id: str,
    transformation_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download a transformed image (authenticated)."""
    output_path = processor.output_dir / "users" / current_user.id / f"{upload_id}_{transformation_type}.jpg"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Transformed image not found")
    
    return FileResponse(
        path=str(output_path),
        filename=f"{upload_id}_{transformation_type}.jpg",
        media_type="image/jpeg"
    )


@app.get("/preview/{upload_id}")
async def get_image_preview(
    upload_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get image preview (authenticated)."""
    # Find uploaded file in user's directory
    user_upload_dir = processor.upload_dir / current_user.id
    upload_path = None
    for file_path in user_upload_dir.glob(f"{upload_id}.*"):
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
async def list_uploads(current_user: User = Depends(get_current_active_user)):
    """List all uploads for the current user."""
    user_uploads = [
        {
            "upload_id": upload_id,
            "status": status_obj.status,
            "progress": status_obj.progress,
            "message": status_obj.message,
            "completed_at": status_obj.completed_at
        }
        for upload_id, status_obj in processor.active_uploads.items()
        if status_obj.user_id == current_user.id
    ]
    
    return {"uploads": user_uploads}


@app.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@app.get("/admin/users")
async def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """List all users (admin only)."""
    return {"users": list(auth_manager.users.values())}


if __name__ == "__main__":
    print("🚀 Starting Authenticated File Upload & Image Processing API")
    print("Features:")
    print("  - OAuth2 authentication with JWT tokens")
    print("  - Social network login (Google, GitHub, Facebook)")
    print("  - Role-based access control (RBAC)")
    print("  - User-specific file storage")
    print("  - Secure file upload and processing")
    print("\nEndpoints:")
    print("  - GET / - Web interface with authentication")
    print("  - POST /token - Login endpoint")
    print("  - POST /oauth2/token - Social login endpoint")
    print("  - POST /upload - Upload file (authenticated)")
    print("  - POST /process/{upload_id} - Process image (authenticated)")
    print("  - GET /status/{upload_id} - Get status (authenticated)")
    print("  - GET /download/{upload_id}/{type} - Download result (authenticated)")
    print("  - GET /users/me - Get current user info")
    print("  - GET /admin/users - List all users (admin only)")
    
    uvicorn.run(
        "authenticated_file_upload_api:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    ) 