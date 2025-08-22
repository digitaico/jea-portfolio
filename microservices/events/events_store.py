import json
from datetime import datetime
from typing import List, Dict, Any

class EventStore:
    def __init__(self):
        self.events = []

    async def store_event(self, event):
        event_record = {
            "id": len(self.events) + 1,
            "timestamp": datetime.now().isoformat(),
            "event": event
        }
        self.events.append(event_record)
        print(f"Event stored: {event.get('event_type')}")
    
    async def get_events_by_type(self, event_type):
        return [e for e in self.events if e['event']['event_type'] == event_type]

    async def replay_events(self, service_name):
        print(f"Replaying events for {service_name}")
        for event_record in self.events:
            print(f"Replaying {event_record['event']['event_type']} ")
    
    async def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all stored events"""
        return self.events
    
    async def clear_events(self) -> None:
        """Clear all events (useful for testing)"""
        self.events.clear()
        self.event_counter = 0
        print("🗑️ All events cleared")