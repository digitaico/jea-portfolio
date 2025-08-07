#!/usr/bin/env python3
"""
Authentication Service for microservices architecture.

This service handles user authentication, JWT token management,
and authorization.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext

from shared.models import (
    User, Token, TokenData, UserRole, UserStatus,
    APIResponse, ServiceHealth
)
from shared.utils import Logger, EventBus, ServiceHealth as HealthMonitor


# Initialize logger
logger = Logger("auth-service", os.getenv("LOG_LEVEL", "INFO"))

# Initialize event bus
event_bus = EventBus(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory storage (in production, use a database)
users = {}
tokens = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Authentication Service")
    
    # Create sample users with hashed passwords
    await create_sample_users()
    
    yield
    logger.info("Shutting down Authentication Service")


# Create FastAPI app
app = FastAPI(
    title="Authentication Service",
    description="Service for user authentication and authorization",
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


class UserLogin(BaseModel):
    """User login model."""
    email: str
    password: str


class UserRegister(BaseModel):
    """User registration model."""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class TokenRefresh(BaseModel):
    """Token refresh model."""
    refresh_token: str


async def create_sample_users():
    """Create sample users with hashed passwords."""
    sample_users = [
        {
            "id": "admin-001",
            "email": "admin@example.com",
            "username": "admin",
            "full_name": "System Administrator",
            "password": "admin123",
            "role": UserRole.ADMIN,
            "status": UserStatus.ACTIVE
        },
        {
            "id": "user-001",
            "email": "user@example.com",
            "username": "user",
            "full_name": "Regular User",
            "password": "user123",
            "role": UserRole.USER,
            "status": UserStatus.ACTIVE
        },
        {
            "id": "premium-001",
            "email": "premium@example.com",
            "username": "premium",
            "full_name": "Premium User",
            "password": "premium123",
            "role": UserRole.PREMIUM,
            "status": UserStatus.ACTIVE
        }
    ]
    
    for user_data in sample_users:
        hashed_password = pwd_context.hash(user_data["password"])
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
        users[user.id] = {
            **user.dict(),
            "hashed_password": hashed_password
        }
    
    logger.info(f"Created {len(sample_users)} sample users")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    if user_id not in users:
        raise credentials_exception
    
    user_data = users[user_id]
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    # Find user by email
    user_data = None
    for user in users.values():
        if user["email"] == email:
            user_data = user
            break
    
    if not user_data:
        return None
    
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint."""
    return APIResponse(
        success=True,
        message="Authentication Service is running",
        data={
            "service": "auth-service",
            "version": "1.0.0",
            "status": "healthy"
        }
    )


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Health check endpoint."""
    health = HealthMonitor("auth-service", "1.0.0")
    return health.get_health()


@app.post("/register", response_model=APIResponse)
async def register(user_data: UserRegister):
    """Register a new user."""
    try:
        # Check if email already exists
        for user in users.values():
            if user["email"] == user_data.email:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            if user["username"] == user_data.username:
                raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        users[user.id] = {
            **user.dict(),
            "hashed_password": hashed_password
        }
        
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
        
        logger.info(f"User registered: {user.id} ({user.email})")
        
        return APIResponse(
            success=True,
            message="User registered successfully",
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/login", response_model=APIResponse)
async def login(user_credentials: UserLogin):
    """Login user and return tokens."""
    try:
        # Authenticate user
        user = await authenticate_user(user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )
        
        # Store refresh token
        tokens[refresh_token] = {
            "user_id": user.id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        }
        
        # Update last login
        users[user.id]["last_login"] = datetime.utcnow()
        
        # Publish login event
        await event_bus.publish_event(
            "user.login",
            {
                "user_id": user.id,
                "email": user.email,
                "login_time": datetime.utcnow().isoformat()
            },
            user_id=user.id
        )
        
        logger.info(f"User logged in: {user.id} ({user.email})")
        
        token_data = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
            user=user
        )
        
        return APIResponse(
            success=True,
            message="Login successful",
            data=token_data.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/token", response_model=APIResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login."""
    try:
        # Authenticate user
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        # Update last login
        users[user.id]["last_login"] = datetime.utcnow()
        
        # Publish login event
        await event_bus.publish_event(
            "user.login",
            {
                "user_id": user.id,
                "email": user.email,
                "login_time": datetime.utcnow().isoformat()
            },
            user_id=user.id
        )
        
        logger.info(f"User logged in via OAuth2: {user.id} ({user.email})")
        
        return APIResponse(
            success=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": user.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/refresh", response_model=APIResponse)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token."""
    try:
        # Verify refresh token
        payload = verify_token(token_data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Check if token exists in storage
        if token_data.refresh_token not in tokens:
            raise HTTPException(status_code=401, detail="Refresh token not found")
        
        token_info = tokens[token_data.refresh_token]
        if datetime.utcnow() > token_info["expires_at"]:
            # Remove expired token
            del tokens[token_data.refresh_token]
            raise HTTPException(status_code=401, detail="Refresh token expired")
        
        user_id = payload.get("sub")
        if user_id not in users:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_data = users[user_id]
        user = User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        # Publish token refreshed event
        await event_bus.publish_event(
            "token.refreshed",
            {
                "user_id": user.id,
                "email": user.email,
                "refresh_time": datetime.utcnow().isoformat()
            },
            user_id=user.id
        )
        
        logger.info(f"Token refreshed for user: {user.id}")
        
        return APIResponse(
            success=True,
            message="Token refreshed successfully",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": user.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@app.post("/validate")
async def validate_token(token: str):
    """Validate JWT token."""
    try:
        payload = verify_token(token)
        if not payload or payload.get("type") != "access":
            return APIResponse(
                success=False,
                message="Invalid token",
                data={"valid": False}
            )
        
        user_id = payload.get("sub")
        if user_id not in users:
            return APIResponse(
                success=False,
                message="User not found",
                data={"valid": False}
            )
        
        user_data = users[user_id]
        user = User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
        
        return APIResponse(
            success=True,
            message="Token is valid",
            data={
                "valid": True,
                "user": user.dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return APIResponse(
            success=False,
            message="Token validation failed",
            data={"valid": False}
        )


@app.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user."""
    try:
        # In a real implementation, you would invalidate the token
        # For now, we'll just log the logout event
        
        # Publish logout event
        await event_bus.publish_event(
            "user.logout",
            {
                "user_id": current_user.id,
                "email": current_user.email,
                "logout_time": datetime.utcnow().isoformat()
            },
            user_id=current_user.id
        )
        
        logger.info(f"User logged out: {current_user.id} ({current_user.email})")
        
        return APIResponse(
            success=True,
            message="Logout successful"
        )
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@app.get("/me", response_model=APIResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    try:
        return APIResponse(
            success=True,
            message="Current user information",
            data=current_user.dict()
        )
        
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current user")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
