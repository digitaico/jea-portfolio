import json
import time
import os
import shutil
from pathlib import Path
from datetime import datetime

from shared.utils.redis_client import RedisClient
from shared.utils.logger import setup_logger
from shared.constants.events import *
from shared.constants.dicom_tags import METADATA_TAGS
from src.extractors.metadata_extractor import MetadataExtractor
from src.utils.config import Config

# Setup logging
logger = setup_logger(__name__)

class DescriptorService:
    def __init__(self):
        self.config = Config()
        self.redis_client = RedisClient()
        self.metadata_extractor = MetadataExtractor()
        self.running = True
        
    def start(self):
        """Start the descriptor service"""
        logger.info("Descriptor service starting...")
        
        # Subscribe to validation channel
        pubsub = self.redis_client.subscribe("validation")
        
        logger.info("Subscribed to validation channel")
        logger.info("Descriptor service started successfully")
        
        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    self.process_message(message["data"])
        except KeyboardInterrupt:
            logger.info("Descriptor service stopping...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in descriptor service: {e}")
            self.running = False
        finally:
            pubsub.close()
    
    def process_message(self, message_data: str):
        """Process a message from the validation channel"""
        try:
            message = json.loads(message_data)
            study_id = message["study_id"]
            file_path = message["file_path"]
            validation_details = message.get("validation_details", {})
            
            logger.info(f"Processing study {study_id} from {file_path}")
            
            # Check if validation was successful
            if not validation_details.get("is_valid", False):
                logger.info(f"Skipping study {study_id} - validation failed")
                return
            
            # Update status to processing
            self.redis_client.set_status(study_id, "processing")
            
            # Extract metadata
            metadata = self.metadata_extractor.extract(file_path)
            
            # Publish described event
            event_data = {
                "study_id": study_id,
                "file_path": file_path,
                "metadata": metadata,
                "validation_details": validation_details
            }
            
            self.redis_client.publish("described", event_data)
            self.redis_client.set_status(study_id, "described", metadata)
            
            logger.info(f"Study {study_id} described successfully.")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Try to extract study_id from message
            try:
                message = json.loads(message_data)
                study_id = message.get("study_id", "unknown")
                self.redis_client.set_status(study_id, "failed", {"error": str(e)})
            except:
                pass

def main():
    """Main entry point"""
    service = DescriptorService()
    service.start()

if __name__ == "__main__":
    main() 