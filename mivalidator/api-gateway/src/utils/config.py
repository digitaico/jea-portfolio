import os
from typing import List

class Config:
    def __init__(self):
        # Service configuration
        self.service_name = os.getenv("SERVICE_NAME", "api-gateway")
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        
        # File upload configuration
        self.uploads_path = os.getenv("UPLOADS_PATH", "/app/uploads")
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB
        self.allowed_extensions = [".dcm", ".dicom"]
        
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO") 