#!/usr/bin/env python3
"""
Tests for the authentication system.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from auth_system import (
    AuthManager, User, UserRole, UserStatus, AuthProvider,
    TokenData, MockSocialProvider, get_current_user, get_current_active_user
)


class TestAuthManager:
    """Test cases for AuthManager class."""
    
    @pytest.fixture
    def auth_manager(self):
        """Create AuthManager instance for testing."""
        return AuthManager()
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return User(
            id="test_user_001",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            provider=AuthProvider.LOCAL,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_verify_password(self, auth_manager):
        """Test password verification."""
        password = "testpassword123"
        hashed = auth_manager.get_password_hash(password)
        
        assert auth_manager.verify_password(password, hashed) is True
        assert auth_manager.verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self, auth_manager, mock_user):
        """Test access token creation."""
        data = {"sub": mock_user.id, "email": mock_user.email, "role": mock_user.role.value}
        token = auth_manager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded = auth_manager.verify_token(token)
        assert decoded is not None
        assert decoded.user_id == mock_user.id
        assert decoded.email == mock_user.email
        assert decoded.role == mock_user.role.value
    
    def test_create_refresh_token(self, auth_manager, mock_user):
        """Test refresh token creation."""
        data = {"sub": mock_user.id, "email": mock_user.email}
        token = auth_manager.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded = auth_manager.verify_token(token)
        assert decoded is not None
        assert decoded.user_id == mock_user.id
    
    def test_verify_token_invalid(self, auth_manager):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        result = auth_manager.verify_token(invalid_token)
        assert result is None
    
    def test_authenticate_user_valid(self, auth_manager):
        """Test user authentication with valid credentials."""
        user = auth_manager.authenticate_user("user@example.com", "user123")
        assert user is not None
        assert user.email == "user@example.com"
        assert user.username == "user"
    
    def test_authenticate_user_invalid(self, auth_manager):
        """Test user authentication with invalid credentials."""
        user = auth_manager.authenticate_user("user@example.com", "wrongpassword")
        assert user is None
    
    def test_authenticate_user_not_found(self, auth_manager):
        """Test user authentication with non-existent user."""
        user = auth_manager.authenticate_user("nonexistent@example.com", "password")
        assert user is None
    
    def test_authenticate_social_user_new(self, auth_manager):
        """Test social user authentication for new user."""
        provider = AuthProvider.GOOGLE
        token = "mock_google_token_123"
        
        user = auth_manager.authenticate_social_user(provider, token)
        assert user is not None
        assert user.provider == provider
        assert user.provider_id == "google_123456789"
        assert user.email == "user@gmail.com"
    
    def test_authenticate_social_user_existing(self, auth_manager):
        """Test social user authentication for existing user."""
        # First, create a user
        provider = AuthProvider.GOOGLE
        token = "mock_google_token_123"
        user1 = auth_manager.authenticate_social_user(provider, token)
        
        # Then authenticate the same user again
        user2 = auth_manager.authenticate_social_user(provider, token)
        assert user2 is not None
        assert user2.id == user1.id
    
    def test_get_user(self, auth_manager):
        """Test getting user by ID."""
        user = auth_manager.get_user("admin_001")
        assert user is not None
        assert user.email == "admin@example.com"
        assert user.role == UserRole.ADMIN
    
    def test_get_user_not_found(self, auth_manager):
        """Test getting non-existent user."""
        user = auth_manager.get_user("nonexistent_id")
        assert user is None
    
    def test_get_user_by_email(self, auth_manager):
        """Test getting user by email."""
        user = auth_manager.get_user_by_email("user@example.com")
        assert user is not None
        assert user.username == "user"
        assert user.role == UserRole.USER
    
    def test_get_user_by_email_not_found(self, auth_manager):
        """Test getting user by non-existent email."""
        user = auth_manager.get_user_by_email("nonexistent@example.com")
        assert user is None


class TestMockSocialProvider:
    """Test cases for MockSocialProvider class."""
    
    @pytest.fixture
    def social_provider(self):
        """Create MockSocialProvider instance for testing."""
        return MockSocialProvider()
    
    def test_validate_token_valid(self, social_provider):
        """Test token validation with valid token."""
        provider = AuthProvider.GOOGLE
        token = "mock_google_token_123"
        
        user_info = social_provider.validate_token(provider, token)
        assert user_info is not None
        assert user_info["email"] == "user@gmail.com"
        assert user_info["name"] == "John Doe"
    
    def test_validate_token_invalid(self, social_provider):
        """Test token validation with invalid token."""
        provider = AuthProvider.GOOGLE
        token = "invalid_token"
        
        user_info = social_provider.validate_token(provider, token)
        assert user_info is None
    
    def test_exchange_code_for_token(self, social_provider):
        """Test code exchange for token."""
        provider = AuthProvider.GITHUB
        code = "mock_github_code_456"
        
        token = social_provider.exchange_code_for_token(provider, code)
        assert token == "mock_github_token_456"
    
    def test_exchange_code_for_token_invalid(self, social_provider):
        """Test code exchange with invalid code."""
        provider = AuthProvider.GITHUB
        code = "invalid_code"
        
        token = social_provider.exchange_code_for_token(provider, code)
        assert token is None
    
    def test_get_user_info(self, social_provider):
        """Test getting user info from social provider."""
        provider = AuthProvider.FACEBOOK
        token = "mock_facebook_token_789"
        
        user_info = social_provider.get_user_info(provider, token)
        assert user_info is not None
        assert user_info["email"] == "user@facebook.com"
        assert user_info["name"] == "Bob Smith"


class TestAuthDependencies:
    """Test cases for authentication dependencies."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid(self):
        """Test get_current_user with valid token."""
        # This would require mocking the OAuth2PasswordBearer dependency
        # and the token verification process
        pass
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self):
        """Test get_current_active_user with active user."""
        # This would require mocking the user status
        pass
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test get_current_active_user with inactive user."""
        # This would require mocking an inactive user
        pass


if __name__ == "__main__":
    pytest.main([__file__])
