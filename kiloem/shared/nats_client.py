"""
Shared NATS Client Module
Provides NATS connection management, publishing, and subscribing utilities.
"""

import nats
import json
import asyncio
from typing import Callable, Optional, Dict, Any
import os
from datetime import datetime
import uuid

class NATSClient:
    """Shared NATS client with connection management and utilities"""

    def __init__(self):
        self.client: Optional[nats.Nats] = None
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.service_name = os.getenv("SERVICE_NAME", "unknown-service")
        self.subscriptions = []

    async def connect(self):
        """Connect to NATS server"""
        try:
            self.client = await nats.connect(self.nats_url)
            print(f"✅ Connected to NATS at {self.nats_url} from {self.service_name}")
        except Exception as e:
            print(f"❌ Failed to connect to NATS: {e}")
            raise

    async def disconnect(self):
        """Disconnect from NATS server"""
        if self.client:
            await self.client.close()
            print(f"✅ Disconnected from NATS - {self.service_name}")

    async def publish_event(self, subject: str, event_data: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
        """
        Publish an event to NATS with proper formatting

        Args:
            subject: NATS subject (e.g., "appointment.scheduled")
            event_data: Event payload dictionary
            correlation_id: Optional correlation ID for tracking

        Returns:
            Generated correlation ID
        """
        if not self.client:
            raise Exception("NATS client not connected")

        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Add standard event metadata
        event_payload = {
            **event_data,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source_service": self.service_name
        }

        # Convert to JSON
        event_json = json.dumps(event_payload)

        # Publish to NATS
        await self.client.publish(subject, event_json.encode())
        print(f"📤 Published event to {subject}: {event_data.get('event_type', subject)}")

        return correlation_id

    async def subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """
        Subscribe to NATS subject

        Args:
            subject: Subject pattern to subscribe to
            callback: Async function to handle messages
            queue_group: Optional queue group for load balancing
        """
        if not self.client:
            raise Exception("NATS client not connected")

        subscription = await self.client.subscribe(subject, cb=callback, queue=queue_group)
        self.subscriptions.append(subscription)
        print(f"📡 Subscribed to {subject} from {self.service_name}")

        return subscription

    async def unsubscribe_all(self):
        """Unsubscribe from all subscriptions"""
        for subscription in self.subscriptions:
            await subscription.unsubscribe()
        self.subscriptions.clear()

# Global NATS client instance
nats_client = NATSClient()

async def get_nats_client() -> NATSClient:
    """Dependency for getting NATS client"""
    return nats_client

async def init_nats():
    """Initialize NATS connection"""
    await nats_client.connect()

async def close_nats():
    """Close NATS connection"""
    await nats_client.disconnect()

# Utility functions for common event operations
async def publish_domain_event(subject: str, event_type: str, data: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
    """Publish a domain event"""
    event_data = {
        "event_type": event_type,
        **data
    }
    return await nats_client.publish_event(subject, event_data, correlation_id)

async def publish_command(subject: str, command_type: str, data: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
    """Publish a command"""
    command_data = {
        "command_type": command_type,
        **data
    }
    return await nats_client.publish_event(subject, command_data, correlation_id)