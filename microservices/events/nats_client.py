import nats
import json
import asyncio
from typing import Callable, Dict, Any

class EventBus:
    def __init__(self, nats_url: str = "nats://nats-server:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.subscriptions: Dict[str, Callable] = {}


    async def connect(self):
        try:
            self.nc = await nats.connect(self.nats_url)
            print(f"Connected to NATS at {self.nats_url}")
        except Exception as e:
            print(f"Failed to connect to NATS: {e}")
            raise

    async def publish(self, subject: str, event: Any):
        if not self.nc:
            await self.connect()
        
        if hasattr(event, 'dict'):
            event_data = event.dict()
        else:
            event_data = event

        try:
            await self.nc.publish(subject, json.dumps(event_data).encode())
            print(f"Published to {subject}: {event_data}")
        finally:
            await self.nc.flush()

    async def subscribe(self, subject: str, callback: Callable):
        if not self.nc:
            await self.connect()

        async def message_handler(msg):
            try:
                data = json.loads(msg.data.decode())
                print(f"Received message on {msg.subject}: {data}")
                await callback(data)
            except Exception as e:
                print(f"Failed to decode message {e}")

        await self.nc.subscribe(subject, cb=message_handler)
        print(f"Subscribed to {subject}")

    async def close(self):
        if self.nc:
            await self.nc.close()
            print("NATS connection closed.")