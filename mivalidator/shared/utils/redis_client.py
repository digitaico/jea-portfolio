import redis
import json
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        
    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish a message to a Redis channel"""
        try:
            message_str = json.dumps(message)
            result = self.client.publish(channel, message_str)
            logger.info(f"Published message to channel {channel}: {message}")
            return result
        except Exception as e:
            logger.error(f"Failed to publish message to channel {channel}: {e}")
            raise
    
    def subscribe(self, channel: str):
        """Subscribe to a Redis channel"""
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            raise
    
    def set_status(self, study_id: str, status: str, details: Optional[Dict] = None) -> bool:
        """Set status for a study"""
        try:
            status_data = {
                "status": status,
                "timestamp": self._get_timestamp(),
                "details": details or {}
            }
            key = f"status:{study_id}"
            self.client.set(key, json.dumps(status_data))
            logger.info(f"Set status for study {study_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to set status for study {study_id}: {e}")
            return False
    
    def get_status(self, study_id: str) -> Optional[Dict]:
        """Get status for a study"""
        try:
            key = f"status:{study_id}"
            status_data = self.client.get(key)
            if status_data:
                return json.loads(status_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get status for study {study_id}: {e}")
            return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() 