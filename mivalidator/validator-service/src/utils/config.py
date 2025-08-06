import os

class Config:
    def __init__(self):
        # Service configuration
        self.service_name = os.getenv("SERVICE_NAME", "validator-service")
        
        # File paths
        self.uploads_path = os.getenv("UPLOADS_PATH", "/app/uploads")
        
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Status service configuration
        self.status_service_url = os.getenv("STATUS_SERVICE_URL", "http://status-service:8003")
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO") 