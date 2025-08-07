#!/usr/bin/env python3
"""
User Service for microservices architecture.

This service handles user management, profiles, and user-related operations.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.models import (
    User, UserCreate, UserUpdate, UserRole, UserStatus,
    APIResponse, ServiceHealth, PaginatedResponse
)
from shared.utils import Logger, EventBus, ServiceHealth as HealthMonitor


# Initialize logger
logger = Logger("user-service", os.getenv("LOG_LEVEL", "INFO"))

# Initialize event bus
event_bus = EventBus(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# In-memory storage (in production, use a database)
users = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting User Service")
    
    # Create some sample users
    await create_sample_users()
    
    yield
    logger.info("Shutting down User Service")


# Create FastAPI app
app = FastAPI(
    title="User Service",
    description="Service for user management",
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


async def create_sample_users():
    """Create sample users for testing."""
    sample_users = [
        {
            "id": "admin-001",
            "email": "admin@example.com",
            "username": "admin",
            "full_name": "System Administrator",
            "role": UserRole.ADMIN,
            "status": UserStatus.ACTIVE
        },
        {
            "id": "user-001",
            "email": "user@example.com",
            "username": "user",
            "full_name": "Regular User",
            "role": UserRole.USER,
            "status": UserStatus.ACTIVE
        },
        {
            "id": "premium-001",
            "email": "premium@example.com",
            "username": "premium",
            "full_name": "Premium User",
            "role": UserRole.PREMIUM,
            "status": UserStatus.ACTIVE
        }
    ]
    
    for user_data in sample_users:
        user = User(
            id=user_data["id"],
            email=user_data["email"],
            username=user_data["username"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            status=user_data["status"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        users[user.id] = user.dict()
    
    logger.info(f"Created {len(sample_users)} sample users")


async def get_current_user(user_id: str) -> User:
    """Get current user by ID."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = users[user_id]
    return User(**user_data)


async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email."""
    for user_data in users.values():
        if user_data["email"] == email:
            return User(**user_data)
    return None


async def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username."""
    for user_data in users.values():
        if user_data["username"] == username:
            return User(**user_data)
    return None


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint."""
    return APIResponse(
        success=True,
        message="User Service is running",
        data={
            "service": "user-service",
            "version": "1.0.0",
            "status": "healthy"
        }
    )


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Health check endpoint."""
    health = HealthMonitor("user-service", "1.0.0")
    return health.get_health()


@app.post("/users", response_model=APIResponse)
async def create_user(user_data: UserCreate):
    """Create a new user."""
    try:
        # Check if email already exists
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if username already exists
        existing_username = await get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create new user
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            role=user_data.role,
            status=UserStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        users[user.id] = user.dict()
        
        # Publish user created event
        await event_bus.publish_event(
            "user.created",
            {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value
            },
            user_id=user.id
        )
        
        logger.info(f"User created: {user.id} ({user.email})")
        
        return APIResponse(
            success=True,
            message="User created successfully",
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(status_code=500, detail="User creation failed")


@app.get("/users/{user_id}", response_model=APIResponse)
async def get_user(user_id: str):
    """Get user by ID."""
    try:
        user = await get_current_user(user_id)
        
        return APIResponse(
            success=True,
            message="User retrieved successfully",
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@app.get("/me", response_model=APIResponse)
async def get_current_user_info(user_id: str = Depends(get_current_user)):
    """Get current user information."""
    try:
        return APIResponse(
            success=True,
            message="Current user information",
            data=user_id.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current user")


@app.put("/me", response_model=APIResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user information."""
    try:
        # Check if username is being changed and if it's already taken
        if (user_update.username and 
            user_update.username != current_user.username):
            existing_user = await get_user_by_username(user_update.username)
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already taken")
        
        # Update user fields
        user_data = current_user.dict()
        
        if user_update.username:
            user_data["username"] = user_update.username
        if user_update.full_name:
            user_data["full_name"] = user_update.full_name
        if user_update.avatar_url:
            user_data["avatar_url"] = user_update.avatar_url
        if user_update.role:
            user_data["role"] = user_update.role
        if user_update.status:
            user_data["status"] = user_update.status
        
        user_data["updated_at"] = datetime.utcnow()
        
        # Update storage
        users[current_user.id] = user_data
        
        # Publish user updated event
        await event_bus.publish_event(
            "user.updated",
            {
                "user_id": current_user.id,
                "updated_fields": user_update.dict(exclude_unset=True)
            },
            user_id=current_user.id
        )
        
        logger.info(f"User updated: {current_user.id}")
        
        return APIResponse(
            success=True,
            message="User updated successfully",
            data=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@app.delete("/users/{user_id}", response_model=APIResponse)
async def delete_user(user_id: str):
    """Delete a user."""
    try:
        if user_id not in users:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = users[user_id]
        
        # Soft delete - mark as inactive
        user_data["status"] = UserStatus.INACTIVE
        user_data["updated_at"] = datetime.utcnow()
        users[user_id] = user_data
        
        # Publish user deleted event
        await event_bus.publish_event(
            "user.deleted",
            {
                "user_id": user_id,
                "email": user_data["email"],
                "username": user_data["username"]
            },
            user_id=user_id
        )
        
        logger.info(f"User deleted: {user_id}")
        
        return APIResponse(
            success=True,
            message="User deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


@app.get("/users", response_model=APIResponse)
async def list_users(
    page: int = 1,
    size: int = 10,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None
):
    """List users with pagination and filtering."""
    try:
        # Filter users
        filtered_users = list(users.values())
        
        if role:
            filtered_users = [u for u in filtered_users if u["role"] == role]
        
        if status:
            filtered_users = [u for u in filtered_users if u["status"] == status]
        
        # Sort by creation date (newest first)
        filtered_users.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        total = len(filtered_users)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_users = filtered_users[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_users)} users",
            data={
                "users": paginated_users,
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
        logger.error(f"List users failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@app.get("/admin/users", response_model=APIResponse)
async def admin_list_users(
    page: int = 1,
    size: int = 10,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None
):
    """Admin endpoint to list all users."""
    try:
        # This would typically check for admin permissions
        # For now, we'll just call the regular list_users function
        return await list_users(page, size, role, status)
        
    except Exception as e:
        logger.error(f"Admin list users failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@app.get("/users/search")
async def search_users(
    query: str,
    page: int = 1,
    size: int = 10
):
    """Search users by email, username, or full name."""
    try:
        query_lower = query.lower()
        matching_users = []
        
        for user_data in users.values():
            if (query_lower in user_data["email"].lower() or
                query_lower in user_data["username"].lower() or
                (user_data["full_name"] and 
                 query_lower in user_data["full_name"].lower())):
                matching_users.append(user_data)
        
        # Sort by creation date (newest first)
        matching_users.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        total = len(matching_users)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_users = matching_users[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1
        
        return APIResponse(
            success=True,
            message=f"Found {len(paginated_users)} users matching '{query}'",
            data={
                "users": paginated_users,
                "query": query,
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
        logger.error(f"Search users failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to search users")


@app.get("/stats")
async def get_user_stats():
    """Get user statistics."""
    try:
        total_users = len(users)
        active_users = len([u for u in users.values() if u["status"] == UserStatus.ACTIVE])
        inactive_users = len([u for u in users.values() if u["status"] == UserStatus.INACTIVE])
        
        role_counts = {}
        for user_data in users.values():
            role = user_data["role"]
            role_counts[role] = role_counts.get(role, 0) + 1
        
        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "role_distribution": role_counts
        }
        
        return APIResponse(
            success=True,
            message="User statistics",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Get user stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
