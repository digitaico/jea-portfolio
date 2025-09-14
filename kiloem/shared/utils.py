"""
Shared Utilities Module
Common helper functions, configurations, and utilities used across services.
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

# Configuration Management
class Config:
    """Centralized configuration management"""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db")

    # NATS
    NATS_URL: str = os.getenv("NATS_URL", "nats://localhost:4222")

    # Services
    APPOINTMENT_SERVICE_URL: str = os.getenv("APPOINTMENT_SERVICE_URL", "http://appointment-service:8010")
    NOTIFICATIONS_SERVICE_URL: str = os.getenv("NOTIFICATIONS_SERVICE_URL", "http://notifications-service:8011")
    PATIENT_SERVICE_URL: str = os.getenv("PATIENT_SERVICE_URL", "http://patient-service:8012")
    DOCTOR_SERVICE_URL: str = os.getenv("DOCTOR_SERVICE_URL", "http://doctor-service:8013")
    EVENT_STORE_SERVICE_URL: str = os.getenv("EVENT_STORE_SERVICE_URL", "http://event-store-service:8014")

    # Service Identity
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "unknown-service")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# JSON Utilities
class JSONUtils:
    """JSON handling utilities"""

    @staticmethod
    def serialize_datetime(obj):
        """JSON serializer for datetime objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    @staticmethod
    def dumps(data: Any, indent: Optional[int] = None) -> str:
        """Enhanced JSON dumps with datetime support"""
        return json.dumps(data, default=JSONUtils.serialize_datetime, indent=indent)

    @staticmethod
    def loads(json_str: str) -> Any:
        """Enhanced JSON loads"""
        return json.loads(json_str)

# ID Generation
class IDGenerator:
    """ID generation utilities"""

    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID string"""
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def generate_short_id(prefix: str = "", length: int = 8) -> str:
        """Generate short ID with optional prefix"""
        import random
        import string

        chars = string.ascii_letters + string.digits
        short_id = ''.join(random.choice(chars) for _ in range(length))

        return f"{prefix}{short_id}" if prefix else short_id

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate correlation ID for request tracking"""
        return IDGenerator.generate_uuid()

# Time Utilities
class TimeUtils:
    """Time and date utilities"""

    @staticmethod
    def now_utc() -> datetime:
        """Get current UTC datetime"""
        return datetime.now(timezone.utc)

    @staticmethod
    def now_iso() -> str:
        """Get current UTC datetime as ISO string"""
        return TimeUtils.now_utc().isoformat()

    @staticmethod
    def parse_iso(iso_string: str) -> datetime:
        """Parse ISO datetime string"""
        if iso_string.endswith('Z'):
            iso_string = iso_string[:-1] + '+00:00'
        return datetime.fromisoformat(iso_string)

    @staticmethod
    def format_duration(minutes: int) -> str:
        """Format duration in minutes to human readable string"""
        if minutes < 60:
            return f"{minutes} minutes"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minutes"

# Validation Utilities
class ValidationUtils:
    """Data validation utilities"""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number format (basic)"""
        import re
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Check if it's 10-15 digits (international format)
        return 10 <= len(digits_only) <= 15

    @staticmethod
    def is_future_datetime(dt: datetime) -> bool:
        """Check if datetime is in the future"""
        return dt > TimeUtils.now_utc()

    @staticmethod
    def sanitize_string(text: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not text:
            return ""
        # Remove leading/trailing whitespace
        text = text.strip()
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        return text

# Logging Utilities
class LoggingUtils:
    """Logging utilities and formatters"""

    @staticmethod
    def format_event_log(event_type: str, data: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
        """Format event log message"""
        base_msg = f"Event: {event_type}"
        if correlation_id:
            base_msg += f" [Correlation: {correlation_id}]"
        if data:
            base_msg += f" | Data: {JSONUtils.dumps(data, indent=0)}"
        return base_msg

    @staticmethod
    def format_error_log(error: Exception, context: Optional[str] = None) -> str:
        """Format error log message"""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg = f"{context} - {error_msg}"
        return error_msg

    @staticmethod
    def format_request_log(method: str, path: str, status_code: int, duration: float) -> str:
        """Format HTTP request log message"""
        return f"{method} {path} -> {status_code} ({duration:.2f}s)"

# Health Check Utilities
class HealthCheck:
    """Health check utilities"""

    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from .database import engine
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "database": str(e)}

    @staticmethod
    async def check_nats() -> Dict[str, Any]:
        """Check NATS connectivity"""
        try:
            from .nats_client import nats_client
            if nats_client.client and nats_client.client.is_connected:
                return {"status": "healthy", "nats": "connected"}
            else:
                return {"status": "unhealthy", "nats": "disconnected"}
        except Exception as e:
            return {"status": "unhealthy", "nats": str(e)}

    @staticmethod
    async def overall_health() -> Dict[str, Any]:
        """Get overall system health"""
        db_health = await HealthCheck.check_database()
        nats_health = await HealthCheck.check_nats()

        overall_status = "healthy"
        if db_health["status"] == "unhealthy" or nats_health["status"] == "unhealthy":
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": TimeUtils.now_iso(),
            "checks": {
                "database": db_health,
                "nats": nats_health
            }
        }

# File System Utilities
class FileUtils:
    """File system utilities"""

    @staticmethod
    def ensure_directory(path: str) -> Path:
        """Ensure directory exists, create if not"""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Get SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

# Constants
class Constants:
    """Application constants"""

    # Appointment statuses
    APPOINTMENT_STATUSES = ["scheduled", "confirmed", "in_progress", "completed", "cancelled", "no_show"]

    # Notification types
    NOTIFICATION_TYPES = ["appointment_scheduled", "appointment_updated", "appointment_cancelled", "reminder"]

    # Service ports
    SERVICE_PORTS = {
        "appointment": 8010,
        "notifications": 8011,
        "patient": 8012,
        "doctor": 8013,
        "event_store": 8014,
        "nginx": 86
    }

    # Default values
    DEFAULT_APPOINTMENT_DURATION = 30  # minutes
    MAX_APPOINTMENT_DURATION = 480  # 8 hours
    MIN_APPOINTMENT_DURATION = 15  # 15 minutes

# Export commonly used utilities
__all__ = [
    "Config",
    "JSONUtils",
    "IDGenerator",
    "TimeUtils",
    "ValidationUtils",
    "LoggingUtils",
    "HealthCheck",
    "FileUtils",
    "Constants"
]