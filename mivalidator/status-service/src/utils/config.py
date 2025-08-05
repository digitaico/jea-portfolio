import os

class Config:
    def __init__(self):
        # Service configuration
        self.service_name = os.getenv("SERVICE_NAME", "status-service")
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8003"))
        
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO") 