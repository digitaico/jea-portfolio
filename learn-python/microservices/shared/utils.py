#!/usr/bin/env python3
"""
Shared utilities for microservices architecture.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import redis
import httpx
from fastapi import HTTPException, Request


class RedisManager:
    """Redis connection manager for microservices."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        try:
            parsed_url = urlparse(self.redis_url)
            self.redis_client = redis.Redis(
                host=parsed_url.hostname or "localhost",
                port=parsed_url.port or 6379,
                password=parsed_url.password,
                db=int(parsed_url.path[1:]) if parsed_url.path else 0,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise
    
    def publish_event(self, channel: str, event: Dict[str, Any]) -> bool:
        """Publish event to Redis channel."""
        try:
            event_json = json.dumps(event)
            result = self.redis_client.publish(channel, event_json)
            return result > 0
        except Exception as e:
            logging.error(f"Failed to publish event: {e}")
            return False
    
    def subscribe_to_channel(self, channel: str):
        """Subscribe to Redis channel."""
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logging.error(f"Failed to subscribe to channel: {e}")
            raise
    
    def set_cache(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set cache value."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.redis_client.setex(key, expire, value)
        except Exception as e:
            logging.error(f"Failed to set cache: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value."""
        try:
            value = self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logging.error(f"Failed to get cache: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete cache value."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logging.error(f"Failed to delete cache: {e}")
            return False


class EventBus:
    """Event bus for microservices communication."""
    
    def __init__(self, redis_url: str = None):
        self.redis_manager = RedisManager(redis_url)
        self.service_name = os.getenv("SERVICE_NAME", "unknown")
    
    def publish_event(self, event_type: str, data: Dict[str, Any], 
                     user_id: Optional[str] = None, correlation_id: Optional[str] = None) -> bool:
        """Publish event to event bus."""
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "source": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "status": "pending",
            "correlation_id": correlation_id,
            "user_id": user_id
        }
        
        # Publish to event bus channel
        success = self.redis_manager.publish_event("event_bus", event)
        
        if success:
            logging.info(f"Event published: {event_type} by {self.service_name}")
        else:
            logging.error(f"Failed to publish event: {event_type}")
        
        return success
    
    def subscribe_to_events(self, event_types: list = None):
        """Subscribe to events."""
        channel = "event_bus"
        pubsub = self.redis_manager.subscribe_to_channel(channel)
        
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    event = json.loads(message["data"])
                    if event_types is None or event["type"] in event_types:
                        yield event
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to decode event: {e}")


class HTTPClient:
    """HTTP client for service-to-service communication."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get(self, url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make GET request."""
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logging.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def post(self, url: str, data: Dict[str, Any] = None, 
                   headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make POST request."""
        try:
            response = await self.client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logging.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def put(self, url: str, data: Dict[str, Any] = None, 
                  headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make PUT request."""
        try:
            response = await self.client.put(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logging.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete(self, url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make DELETE request."""
        try:
            response = await self.client.delete(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logging.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class Logger:
    """Structured logging for microservices."""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(service_name)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        extra_data = {"service": self.service_name, **kwargs}
        self.logger.info(f"{message} | {json.dumps(extra_data)}")
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        extra_data = {"service": self.service_name, **kwargs}
        self.logger.error(f"{message} | {json.dumps(extra_data)}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        extra_data = {"service": self.service_name, **kwargs}
        self.logger.warning(f"{message} | {json.dumps(extra_data)}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        extra_data = {"service": self.service_name, **kwargs}
        self.logger.debug(f"{message} | {json.dumps(extra_data)}")


class ServiceHealth:
    """Service health monitoring."""
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()
    
    def get_health(self) -> Dict[str, Any]:
        """Get service health status."""
        uptime = time.time() - self.start_time
        
        # Get memory usage (simplified)
        try:
            import psutil
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            cpu_usage = psutil.Process().cpu_percent()
        except ImportError:
            memory_usage = None
            cpu_usage = None
        
        return {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": self.version,
            "uptime": uptime,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "dependencies": {}
        }


def generate_correlation_id() -> str:
    """Generate correlation ID for request tracing."""
    return str(uuid.uuid4())


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request headers."""
    return request.headers.get("X-Correlation-ID", generate_correlation_id())


def validate_service_url(url: str) -> bool:
    """Validate service URL."""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    
    raise Exception("Max retries exceeded")
