#!/usr/bin/env python3
"""
Tests for Event Bus service.
"""

import pytest
import json
from fastapi.testclient import TestClient

from event_bus.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestEventBus:
    """Test cases for Event Bus."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event-bus" in data["data"]["service"]
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "event-bus"
        assert data["status"] == "healthy"
    
    def test_publish_event(self, client):
        """Test event publishing."""
        event_data = {
            "type": "test.event",
            "data": {"message": "test"},
            "user_id": "test-user"
        }
        
        response = client.post("/events/publish", json=event_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
    
    def test_get_events(self, client):
        """Test getting events."""
        response = client.get("/events")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]
    
    def test_get_events_with_filters(self, client):
        """Test getting events with filters."""
        response = client.get("/events?limit=10&event_type=test.event")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_specific_event(self, client):
        """Test getting a specific event."""
        # First publish an event
        event_data = {
            "type": "test.event",
            "data": {"message": "test"},
            "user_id": "test-user"
        }
        
        publish_response = client.post("/events/publish", json=event_data)
        event_id = publish_response.json()["data"]["id"]
        
        # Then get the specific event
        response = client.get(f"/events/{event_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == event_id
    
    def test_get_nonexistent_event(self, client):
        """Test getting a non-existent event."""
        response = client.get("/events/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_stats(self, client):
        """Test getting event bus statistics."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_events" in data["data"]
        assert "event_types_count" in data["data"]
    
    def test_clear_events(self, client):
        """Test clearing all events."""
        response = client.delete("/events/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestEventBusValidation:
    """Test Event Bus validation."""
    
    def test_publish_event_invalid_type(self, client):
        """Test publishing event with invalid type."""
        event_data = {
            "type": "invalid.event.type",
            "data": {"message": "test"},
            "user_id": "test-user"
        }
        
        response = client.post("/events/publish", json=event_data)
        # Should either accept or return validation error
        assert response.status_code in [200, 422]
    
    def test_publish_event_missing_fields(self, client):
        """Test publishing event with missing fields."""
        event_data = {
            "type": "test.event"
            # Missing data and user_id
        }
        
        response = client.post("/events/publish", json=event_data)
        # Should return validation error
        assert response.status_code == 422


class TestEventBusErrorHandling:
    """Test Event Bus error handling."""
    
    def test_invalid_endpoint_returns_404(self, client):
        """Test invalid endpoint returns 404."""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        response = client.post("/health")  # POST to GET-only endpoint
        assert response.status_code == 405
    
    def test_invalid_json_in_publish(self, client):
        """Test invalid JSON in publish request."""
        response = client.post("/events/publish", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
