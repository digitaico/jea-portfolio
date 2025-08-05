import logging
import sys
from typing import Optional
import os

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Setup a logger with consistent formatting"""
    logger = logging.getLogger(name)
    
    if logger.handlers:  # Already configured
        return logger
    
    # Set level
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger 