#!/usr/bin/env python3
"""
OAuth2 Authentication System
============================

This module implements OAuth2 authentication with mock social network tokens
for the File Upload & Image Processing API.

Features:
- OAuth2 with JWT tokens
- Mock social network providers (Google, GitHub, Facebook)
- User management and sessions
- Role-based access control (RBAC)
- Token refresh and validation
- Secure password hashing

Supported Providers:
- Google OAuth2
- GitHub OAuth2
- Facebook OAuth2
- Local authentication (username/password)
"""

import os
import time
import uuid
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

# Import from previous stages
from database import db_manager, TransformationHistory
from config import settings


class AuthProvider(str, Enum):
    """Supported authentication providers."""
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"
    LOCAL = "local"


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"
    GUEST = "guest"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """User model."""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    provider: AuthProvider
    provider_id: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    password: Optional[str] = None
    provider: AuthProvider
    provider_id: Optional[str] = None
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: User


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class OAuth2Request(BaseModel):
    """OAuth2 request model."""
    provider: AuthProvider
    code: str
    redirect_uri: str


class MockSocialProvider:
    """Mock social network provider for testing."""
    
    def __init__(self):
        # Mock user database
        self.mock_users = {
            "google": {
                "mock_google_token_123": {
                    "id": "google_123456789",
                    "email": "user@gmail.com",
                    "name": "John Doe",
                    "picture": "https://example.com/avatar.jpg",
                    "provider": "google"
                }
            },
            "github": {
                "mock_github_token_456": {
                    "id": "github_987654321",
                    "email": "developer@github.com",
                    "name": "Jane Developer",
                    "picture": "https://github.com/avatar.jpg",
                    "provider": "github"
                }
            },
            "facebook": {
                "mock_facebook_token_789": {
                    "id": "facebook_555666777",
                    "email": "user@facebook.com",
                    "name": "Bob Smith",
                    "picture": "https://facebook.com/avatar.jpg",
                    "provider": "facebook"
                }
            }
        }
    
    def validate_token(self, provider: AuthProvider, token: str) -> Optional[Dict[str, Any]]:
        """Validate mock social network token."""
        if provider.value in self.mock_users:
            return self.mock_users[provider.value].get(token)
        return None
    
    def exchange_code_for_token(self, provider: AuthProvider, code: str) -> Optional[str]:
        """Exchange authorization code for access token (mock)."""
        # Mock token exchange
        mock_tokens = {
            "google": "mock_google_token_123",
            "github": "mock_github_token_456",
            "facebook": "mock_facebook_token_789"
        }
        return mock_tokens.get(provider.value)
    
    def get_user_info(self, provider: AuthProvider, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from social provider (mock)."""
        return self.validate_token(provider, token)


class AuthManager:
    """Authentication manager."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.social_provider = MockSocialProvider()
        self.secret_key = settings.secret_key or "your-secret-key-here"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
        # Mock user database (in production, this would be in PostgreSQL)
        self.users: Dict[str, User] = {}
        self._initialize_mock_users()
    
    def _initialize_mock_users(self):
        """Initialize mock users for testing."""
        mock_users_data = [
            {
                "id": "admin_001",
                "email": "admin@example.com",
                "username": "admin",
                "full_name": "System Administrator",
                "provider": AuthProvider.LOCAL,
                "role": UserRole.ADMIN,
                "password": "admin123"
            },
            {
                "id": "user_001",
                "email": "user@example.com",
                "username": "user",
                "full_name": "Regular User",
                "provider": AuthProvider.LOCAL,
                "role": UserRole.USER,
                "password": "user123"
            },
            {
                "id": "premium_001",
                "email": "premium@example.com",
                "username": "premium",
                "full_name": "Premium User",
                "provider": AuthProvider.LOCAL,
                "role": UserRole.PREMIUM,
                "password": "premium123"
            }
        ]
        
        for user_data in mock_users_data:
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                username=user_data["username"],
                full_name=user_data["full_name"],
                provider=user_data["provider"],
                role=user_data["role"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.users[user_data["id"]] = user
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash password."""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            
            if user_id is None:
                return None
            
            return TokenData(user_id=user_id, email=email, role=role)
        except jwt.PyJWTError:
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        # Find user by email
        user = None
        for u in self.users.values():
            if u.email == email:
                user = u
                break
        
        if not user:
            return None
        
        # For mock users, use simple password comparison
        # In production, you'd use hashed passwords
        mock_passwords = {
            "admin@example.com": "admin123",
            "user@example.com": "user123",
            "premium@example.com": "premium123"
        }
        
        if email in mock_passwords and password == mock_passwords[email]:
            return user
        
        return None
    
    def authenticate_social_user(self, provider: AuthProvider, token: str) -> Optional[User]:
        """Authenticate user with social network token."""
        user_info = self.social_provider.get_user_info(provider, token)
        if not user_info:
            return None
        
        # Check if user exists
        for user in self.users.values():
            if (user.provider == provider and 
                user.provider_id == user_info["id"]):
                return user
        
        # Create new user if doesn't exist
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=user_info["email"],
            username=user_info["name"].lower().replace(" ", "_"),
            full_name=user_info["name"],
            provider=provider,
            provider_id=user_info["id"],
            avatar_url=user_info.get("picture"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.users[user_id] = user
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create new user."""
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            provider=user_data.provider,
            provider_id=user_data.provider_id,
            avatar_url=user_data.avatar_url,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.users[user_id] = user
        return user
    
    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user."""
        user = self.users.get(user_id)
        if not user:
            return None
        
        if user_data.username:
            user.username = user_data.username
        if user_data.full_name:
            user.full_name = user_data.full_name
        if user_data.avatar_url:
            user.avatar_url = user_data.avatar_url
        if user_data.role:
            user.role = user_data.role
        if user_data.status:
            user.status = user_data.status
        
        user.updated_at = datetime.now()
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False


# Global auth manager instance
auth_manager = AuthManager()


# Dependency functions
async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth_manager.verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = auth_manager.get_user(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: UserRole):
    """Decorator to require specific role."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_roles(required_roles: List[UserRole]):
    """Decorator to require one of specific roles."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker 