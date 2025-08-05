import json
import time
import os
from pathlib import Path

from shared.utils.redis_client import RedisClient
from shared.utils.logger import setup_logger
from shared.constants.events import *
from shared.constants.dicom_tags import REQUIRED_TAGS
from src.validators.dicom_validator import DICOMValidator
from src.utils.config import Config

# Setup logging
logger = setup_logger(__name__)

class ValidatorService:
    def __init__(self):
        self.config = Config()
        self.redis_client = RedisClient()
        self.dicom_validator = DICOMValidator()
        self.running = True
        
    def start(self):
        """Start the validator service"""
        logger.info("Validator service starting...")
        
        # Subscribe to uploads channel
        pubsub = self.redis_client.subscribe("uploads")
        
        logger.info("Subscribed to uploads channel")
        logger.info("Validator service started successfully")
        
        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    self.process_message(message["data"])
        except KeyboardInterrupt:
            logger.info("Validator service stopping...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in validator service: {e}")
            self.running = False
        finally:
            pubsub.close()
    
    def process_message(self, message_data: str):
        """Process a message from the uploads channel"""
        try:
            message = json.loads(message_data)
            study_id = message["study_id"]
            file_path = message["file_path"]
            
            logger.info(f"Processing study {study_id} from {file_path}")
            
            # Update status to validating
            self.redis_client.set_status(study_id, "validating")
            
            # Validate the DICOM file
            validation_result = self.dicom_validator.validate(file_path)
            
            if validation_result["is_valid"]:
                # Publish validation success event
                event_data = {
                    "study_id": study_id,
                    "file_path": file_path,
                    "validation_details": validation_result
                }
                
                self.redis_client.publish("validation", event_data)
                self.redis_client.set_status(study_id, "validated", validation_result)
                
                logger.info(f"Study {study_id} validated successfully")
            else:
                # Publish validation failure event
                event_data = {
                    "study_id": study_id,
                    "file_path": file_path,
                    "validation_details": validation_result
                }
                
                self.redis_client.publish("validation", event_data)
                self.redis_client.set_status(study_id, "validation_failed", validation_result)
                
                logger.warning(f"Study {study_id} validation failed: {validation_result['errors']}")
                
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
    service = ValidatorService()
    service.start()

if __name__ == "__main__":
    main() 