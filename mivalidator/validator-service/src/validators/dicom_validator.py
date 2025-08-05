import pydicom
from pathlib import Path
from typing import Dict, List, Any
import os

from shared.constants.dicom_tags import REQUIRED_TAGS
from shared.utils.logger import setup_logger

logger = setup_logger(__name__)

class DICOMValidator:
    def __init__(self):
        self.required_tags = REQUIRED_TAGS
        
    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate a DICOM file"""
        try:
            logger.info(f"Attempting to validate file: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return {
                    "is_valid": False,
                    "errors": [f"File not found: {file_path}"],
                    "missing_tags": []
                }
            
            # Try to read the DICOM file
            try:
                logger.info(f"Attempting to read DICOM file: {file_path}")
                dataset = pydicom.dcmread(str(file_path))
            except Exception as e:
                logger.error(f"Error reading DICOM file {file_path}: {e}")
                return {
                    "is_valid": False,
                    "errors": [f"Invalid DICOM file or error reading: {str(e)}"],
                    "missing_tags": []
                }
            
            # Check for required tags
            missing_tags = self._check_required_tags(dataset)
            
            if missing_tags:
                return {
                    "is_valid": False,
                    "errors": [f"Missing required tags: {', '.join(missing_tags)}"],
                    "missing_tags": missing_tags
                }
            
            # Additional validation checks
            validation_errors = self._additional_validation(dataset)
            
            if validation_errors:
                return {
                    "is_valid": False,
                    "errors": validation_errors,
                    "missing_tags": []
                }
            
            return {
                "is_valid": True,
                "errors": [],
                "missing_tags": [],
                "file_size": file_path.stat().st_size,
                "modality": getattr(dataset, 'Modality', 'Unknown'),
                "study_date": getattr(dataset, 'StudyDate', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error validating DICOM file {file_path}: {e}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "missing_tags": []
            }
    
    def _check_required_tags(self, dataset: pydicom.Dataset) -> List[str]:
        """Check if all required tags are present"""
        missing_tags = []
        
        for tag_name, tag_value in self.required_tags.items():
            if not hasattr(dataset, tag_name.replace('_', '')):
                missing_tags.append(tag_name)
        
        return missing_tags
    
    def _additional_validation(self, dataset: pydicom.Dataset) -> List[str]:
        """Perform additional validation checks"""
        errors = []
        
        # Check if file has basic DICOM structure
        if not hasattr(dataset, 'SOPClassUID'):
            errors.append("Missing SOPClassUID")
        
        # Check if file has transfer syntax
        if not hasattr(dataset, 'file_meta'):
            errors.append("Missing file meta information")
        
        return errors 