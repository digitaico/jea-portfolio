#!/usr/bin/env python3
"""
Shared models for microservices architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for the event bus."""
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # Authentication events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    TOKEN_REFRESHED = "token.refreshed"
    
    # Image processing events
    IMAGE_UPLOADED = "image.uploaded"
    IMAGE_PROCESSING_STARTED = "image.processing.started"
    IMAGE_PROCESSING_COMPLETED = "image.processing.completed"
    IMAGE_PROCESSING_FAILED = "image.processing.failed"
    IMAGE_DOWNLOADED = "image.downloaded"
    
    # Notification events
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"


class EventStatus(str, Enum):
    """Event status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"
    GUEST = "guest"


class UserStatus(str, Enum):
    """User status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Event(BaseModel):
    """Event model for the event bus."""
    id: str = Field(..., description="Unique event ID")
    type: EventType = Field(..., description="Event type")
    source: str = Field(..., description="Service that generated the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    status: EventStatus = Field(default=EventStatus.PENDING, description="Event status")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    user_id: Optional[str] = Field(None, description="User ID associated with the event")


class User(BaseModel):
    """User model."""
    id: str = Field(..., description="Unique user ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="User status")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class UserCreate(BaseModel):
    """User creation model."""
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    password: Optional[str] = Field(None, description="Password")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    role: Optional[UserRole] = Field(None, description="User role")
    status: Optional[UserStatus] = Field(None, description="User status")


class Token(BaseModel):
    """Token model."""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    user: User = Field(..., description="User information")


class ImageUpload(BaseModel):
    """Image upload model."""
    id: str = Field(..., description="Unique upload ID")
    user_id: str = Field(..., description="User ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    status: str = Field(default="uploaded", description="Upload status")


class ImageProcessing(BaseModel):
    """Image processing model."""
    id: str = Field(..., description="Unique processing ID")
    upload_id: str = Field(..., description="Upload ID")
    user_id: str = Field(..., description="User ID")
    transformation_type: str = Field(..., description="Transformation type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Processing parameters")
    status: str = Field(default="pending", description="Processing status")
    progress: int = Field(default=0, description="Processing progress (0-100)")
    output_path: Optional[str] = Field(None, description="Output file path")
    processing_time: Optional[int] = Field(None, description="Processing time in milliseconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class Notification(BaseModel):
    """Notification model."""
    id: str = Field(..., description="Unique notification ID")
    user_id: str = Field(..., description="User ID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    status: str = Field(default="pending", description="Notification status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")


class ServiceHealth(BaseModel):
    """Service health model."""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Service uptime in seconds")
    memory_usage: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")


class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    items: List[Dict[str, Any]] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")
