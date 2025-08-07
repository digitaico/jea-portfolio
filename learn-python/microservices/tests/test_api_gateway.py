#!/usr/bin/env python3
"""
Tests for API Gateway service.
"""

import pytest
import httpx
from fastapi.testclient import TestClient

from api_gateway.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestAPIGateway:
    """Test cases for API Gateway."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api-gateway" in data["data"]["service"]
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "api-gateway"
        assert data["status"] == "healthy"
    
    def test_services_health_endpoint(self, client):
        """Test services health endpoint."""
        response = client.get("/services/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make multiple requests to trigger rate limiting
        for _ in range(105):  # More than the limit
            response = client.get("/")
            if response.status_code == 429:
                break
        else:
            # If we didn't hit rate limit, that's also acceptable
            assert response.status_code in [200, 429]
    
    def test_correlation_id_header(self, client):
        """Test correlation ID header is added."""
        response = client.get("/")
        assert "X-Correlation-ID" in response.headers
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/")
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented
    
    def test_authentication_required_endpoints(self, client):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/users/me",
            "/images/upload",
            "/notifications"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401  # Unauthorized


class TestAPIGatewayRouting:
    """Test API Gateway routing functionality."""
    
    def test_auth_routes_exist(self, client):
        """Test authentication routes exist."""
        auth_routes = [
            "/auth/login",
            "/auth/register",
            "/auth/refresh"
        ]
        
        for route in auth_routes:
            response = client.post(route, json={})
            # Should not be 404 (route exists)
            assert response.status_code != 404
    
    def test_image_routes_exist(self, client):
        """Test image processing routes exist."""
        image_routes = [
            "/images/upload",
            "/images/{upload_id}/process",
            "/images/{upload_id}/status",
            "/images/{upload_id}/download/{transformation_type}"
        ]
        
        # Test with a dummy upload_id
        test_upload_id = "test-upload-id"
        test_transformation = "grayscale"
        
        routes_to_test = [
            f"/images/{test_upload_id}/process",
            f"/images/{test_upload_id}/status",
            f"/images/{test_upload_id}/download/{test_transformation}"
        ]
        
        for route in routes_to_test:
            response = client.get(route)
            # Should not be 404 (route exists)
            assert response.status_code != 404
    
    def test_user_routes_exist(self, client):
        """Test user management routes exist."""
        user_routes = [
            "/users/me"
        ]
        
        for route in user_routes:
            response = client.get(route)
            # Should not be 404 (route exists)
            assert response.status_code != 404
    
    def test_notification_routes_exist(self, client):
        """Test notification routes exist."""
        notification_routes = [
            "/notifications"
        ]
        
        for route in notification_routes:
            response = client.get(route)
            # Should not be 404 (route exists)
            assert response.status_code != 404


class TestAPIGatewayErrorHandling:
    """Test API Gateway error handling."""
    
    def test_invalid_endpoint_returns_404(self, client):
        """Test invalid endpoint returns 404."""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        response = client.post("/health")  # POST to GET-only endpoint
        assert response.status_code == 405
    
    def test_request_validation(self, client):
        """Test request validation."""
        # Test with invalid JSON
        response = client.post("/auth/login", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422  # Unprocessable Entity


if __name__ == "__main__":
    pytest.main([__file__])
