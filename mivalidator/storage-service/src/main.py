import json
import os
import shutil
from pathlib import Path
from datetime import datetime

from shared.utils.redis_client import RedisClient
from shared.utils.logger import setup_logger
from shared.constants.events import *
from src.utils.config import Config

# Setup logging
logger = setup_logger(__name__)

class StorageService:
    def __init__(self):
        self.config = Config()
        self.redis_client = RedisClient()
        self.running = True
        
    def start(self):
        """Start the storage service"""
        logger.info("Storage service starting...")
        
        # Subscribe to described channel
        pubsub = self.redis_client.subscribe("described")
        
        logger.info("Subscribed to described channel")
        logger.info("Storage service started successfully")
        
        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    self.process_message(message["data"])
        except KeyboardInterrupt:
            logger.info("Storage service stopping...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in storage service: {e}")
            self.running = False
        finally:
            pubsub.close()
    
    def process_message(self, message_data: str):
        """Process a message from the described channel"""
        try:
            message = json.loads(message_data)
            study_id = message["study_id"]
            file_path = message["file_path"]
            metadata = message.get("metadata", {})
            validation_details = message.get("validation_details", {})
            
            logger.info(f"Processing study {study_id} from {file_path}")
            
            # Create archive directory
            archive_dir = Path(self.config.archive_path) / study_id
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy original file to archive
            original_file = Path(file_path)
            archive_file = archive_dir / original_file.name
            shutil.copy2(original_file, archive_file)
            
            # Save metadata to JSON file
            metadata_file = archive_dir / "metadata.json"
            metadata["study_id"] = study_id
            metadata["processing_time"] = datetime.utcnow().isoformat()
            metadata["validation_details"] = validation_details
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Update status to archived
            self.redis_client.set_status(study_id, "archived", {
                "archive_path": str(archive_dir),
                "metadata_file": str(metadata_file)
            })
            
            logger.info(f"Study {study_id} archived successfully at {archive_dir}")
            
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
    service = StorageService()
    service.start()

if __name__ == "__main__":
    main()
