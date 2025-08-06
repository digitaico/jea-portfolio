#!/usr/bin/env python3
"""
API Gateway for microservices architecture.

This service acts as the entry point for all client requests,
routing them to appropriate microservices and handling
authentication, rate limiting, and request/response transformation.
"""

import os
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx

from shared.models import APIResponse, ServiceHealth
from shared.utils import Logger, HTTPClient, get_correlation_id, validate_service_url


# Initialize logger
logger = Logger("api-gateway", os.getenv("LOG_LEVEL", "INFO"))

# Service URLs
SERVICE_URLS = {
    "image": os.getenv("IMAGE_SERVICE_URL", "http://image-service:8002"),
    "user": os.getenv("USER_SERVICE_URL", "http://user-service:8003"),
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8004"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8005"),
    "event_bus": os.getenv("EVENT_BUS_URL", "http://event-bus:8001")
}

# Rate limiting
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # requests per window

# Request tracking
request_counts = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting API Gateway")
    yield
    logger.info("Shutting down API Gateway")


# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="API Gateway for microservices architecture",
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

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)


class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter()


async def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


async def check_rate_limit(request: Request):
    """Check rate limit for client."""
    client_ip = await get_client_ip(request)
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )


async def get_auth_token(request: Request) -> Optional[str]:
    """Extract authentication token from request."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return None


async def validate_token(token: str) -> Dict[str, Any]:
    """Validate JWT token with auth service."""
    if not token:
        return None
    
    try:
        async with HTTPClient() as client:
            response = await client.post(
                f"{SERVICE_URLS['auth']}/validate",
                data={"token": token}
            )
            return response
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return None


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to request."""
    correlation_id = get_correlation_id(request)
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Check rate limit
    await check_rate_limit(request)
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        correlation_id=request.state.correlation_id,
        client_ip=await get_client_ip(request),
        user_agent=request.headers.get("User-Agent", "")
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code}",
        correlation_id=request.state.correlation_id,
        process_time=process_time
    )
    
    return response


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint."""
    return APIResponse(
        success=True,
        message="API Gateway is running",
        data={
            "service": "api-gateway",
            "version": "1.0.0",
            "status": "healthy"
        }
    )


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Health check endpoint."""
    health = ServiceHealth("api-gateway", "1.0.0")
    return health.get_health()


@app.get("/services/health")
async def services_health():
    """Check health of all services."""
    health_status = {}
    
    for service_name, service_url in SERVICE_URLS.items():
        try:
            async with HTTPClient() as client:
                response = await client.get(f"{service_url}/health")
                health_status[service_name] = {
                    "status": "healthy",
                    "response": response
                }
        except Exception as e:
            health_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return APIResponse(
        success=True,
        message="Services health check completed",
        data=health_status
    )


# Authentication routes
@app.post("/auth/login")
async def login(request: Request):
    """Login endpoint."""
    try:
        body = await request.json()
        async with HTTPClient() as client:
            response = await client.post(
                f"{SERVICE_URLS['auth']}/login",
                data=body
            )
            return response
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/auth/register")
async def register(request: Request):
    """Register endpoint."""
    try:
        body = await request.json()
        async with HTTPClient() as client:
            response = await client.post(
                f"{SERVICE_URLS['auth']}/register",
                data=body
            )
            return response
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/auth/refresh")
async def refresh_token(request: Request):
    """Refresh token endpoint."""
    try:
        body = await request.json()
        async with HTTPClient() as client:
            response = await client.post(
                f"{SERVICE_URLS['auth']}/refresh",
                data=body
            )
            return response
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


# User routes
@app.get("/users/me")
async def get_current_user(request: Request):
    """Get current user information."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with HTTPClient() as client:
            response = await client.get(
                f"{SERVICE_URLS['user']}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user information")


@app.put("/users/me")
async def update_current_user(request: Request):
    """Update current user information."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        body = await request.json()
        async with HTTPClient() as client:
            response = await client.put(
                f"{SERVICE_URLS['user']}/me",
                data=body,
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Update user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


# Image processing routes
@app.post("/images/upload")
async def upload_image(request: Request):
    """Upload image endpoint."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Forward the multipart form data
        form_data = await request.form()
        files = await request.files()
        
        async with HTTPClient() as client:
            response = await client.post(
                f"{SERVICE_URLS['image']}/upload",
                data=form_data,
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed")


@app.post("/images/{upload_id}/process")
async def process_image(upload_id: str, request: Request):
    """Process image endpoint."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        body = await request.json()
        async with HTTPClient() as client:
            response = await client.post(
                f"{SERVICE_URLS['image']}/process/{upload_id}",
                data=body,
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(status_code=500, detail="Image processing failed")


@app.get("/images/{upload_id}/status")
async def get_image_status(upload_id: str, request: Request):
    """Get image processing status."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with HTTPClient() as client:
            response = await client.get(
                f"{SERVICE_URLS['image']}/status/{upload_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Get image status failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get image status")


@app.get("/images/{upload_id}/download/{transformation_type}")
async def download_image(upload_id: str, transformation_type: str, request: Request):
    """Download processed image."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with HTTPClient() as client:
            response = await client.get(
                f"{SERVICE_URLS['image']}/download/{upload_id}/{transformation_type}",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Image download failed: {e}")
        raise HTTPException(status_code=500, detail="Image download failed")


# Notification routes
@app.get("/notifications")
async def get_notifications(request: Request):
    """Get user notifications."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with HTTPClient() as client:
            response = await client.get(
                f"{SERVICE_URLS['notification']}/notifications",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Get notifications failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")


@app.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, request: Request):
    """Mark notification as read."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with HTTPClient() as client:
            response = await client.put(
                f"{SERVICE_URLS['notification']}/notifications/{notification_id}/read",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"Mark notification read failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")


# Admin routes
@app.get("/admin/users")
async def list_users(request: Request):
    """List all users (admin only)."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with HTTPClient() as client:
            response = await client.get(
                f"{SERVICE_URLS['user']}/admin/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"List users failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@app.get("/admin/events")
async def list_events(request: Request):
    """List recent events (admin only)."""
    token = await get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with HTTPClient() as client:
            response = await client.get(
                f"{SERVICE_URLS['event_bus']}/events",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
    except Exception as e:
        logger.error(f"List events failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list events")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
