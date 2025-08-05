import pydicom
from pathlib import Path
from typing import Dict, Any
import os

from shared.constants.dicom_tags import METADATA_TAGS
from shared.utils.logger import setup_logger

logger = setup_logger(__name__)

class MetadataExtractor:
    def __init__(self):
        self.metadata_tags = METADATA_TAGS
        
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a DICOM file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read the DICOM file
            dataset = pydicom.dcmread(str(file_path))
            
            # Extract metadata by category
            metadata = {
                "patient_info": self._extract_patient_info(dataset),
                "study_info": self._extract_study_info(dataset),
                "modality_info": self._extract_modality_info(dataset),
                "exposure_info": self._extract_exposure_info(dataset),
                "location_info": self._extract_location_info(dataset)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {
                "patient_info": {},
                "study_info": {},
                "modality_info": {},
                "exposure_info": {},
                "location_info": {},
                "error": str(e)
            }
    
    def _extract_patient_info(self, dataset: pydicom.Dataset) -> Dict[str, Any]:
        """Extract patient information"""
        patient_info = {}
        
        # Extract patient ID
        if hasattr(dataset, 'PatientID'):
            patient_info['patient_id'] = str(dataset.PatientID)
        
        # Extract patient name
        if hasattr(dataset, 'PatientName'):
            patient_info['patient_name'] = str(dataset.PatientName)
        
        # Extract patient birth date
        if hasattr(dataset, 'PatientBirthDate'):
            patient_info['patient_birth_date'] = str(dataset.PatientBirthDate)
        
        # Extract patient sex
        if hasattr(dataset, 'PatientSex'):
            patient_info['patient_sex'] = str(dataset.PatientSex)
        
        # Extract patient age
        if hasattr(dataset, 'PatientAge'):
            patient_info['patient_age'] = str(dataset.PatientAge)
        
        return patient_info
    
    def _extract_study_info(self, dataset: pydicom.Dataset) -> Dict[str, Any]:
        """Extract study information"""
        study_info = {}
        
        # Extract study instance UID
        if hasattr(dataset, 'StudyInstanceUID'):
            study_info['study_instance_uid'] = str(dataset.StudyInstanceUID)
        
        # Extract study date
        if hasattr(dataset, 'StudyDate'):
            study_info['study_date'] = str(dataset.StudyDate)
        
        # Extract study time
        if hasattr(dataset, 'StudyTime'):
            study_info['study_time'] = str(dataset.StudyTime)
        
        # Extract study description
        if hasattr(dataset, 'StudyDescription'):
            study_info['study_description'] = str(dataset.StudyDescription)
        
        # Extract accession number
        if hasattr(dataset, 'AccessionNumber'):
            study_info['accession_number'] = str(dataset.AccessionNumber)
        
        # Extract study ID
        if hasattr(dataset, 'StudyID'):
            study_info['study_id'] = str(dataset.StudyID)
        
        return study_info
    
    def _extract_modality_info(self, dataset: pydicom.Dataset) -> Dict[str, Any]:
        """Extract modality information"""
        modality_info = {}
        
        # Extract modality
        if hasattr(dataset, 'Modality'):
            modality_info['modality'] = str(dataset.Modality)
        
        # Extract manufacturer
        if hasattr(dataset, 'Manufacturer'):
            modality_info['manufacturer'] = str(dataset.Manufacturer)
        
        # Extract model name
        if hasattr(dataset, 'ManufacturerModelName'):
            modality_info['model_name'] = str(dataset.ManufacturerModelName)
        
        # Extract station name
        if hasattr(dataset, 'StationName'):
            modality_info['station_name'] = str(dataset.StationName)
        
        return modality_info
    
    def _extract_exposure_info(self, dataset: pydicom.Dataset) -> Dict[str, Any]:
        """Extract exposure information"""
        exposure_info = {}
        
        # Extract exposure time
        if hasattr(dataset, 'ExposureTime'):
            exposure_info['exposure_time'] = str(dataset.ExposureTime)
        
        # Extract exposure mAs
        if hasattr(dataset, 'ExposureInmAs'):
            exposure_info['exposure_mas'] = str(dataset.ExposureInmAs)
        
        # Extract kVp
        if hasattr(dataset, 'KVP'):
            exposure_info['kvp'] = str(dataset.KVP)
        
        # Extract repetition time
        if hasattr(dataset, 'RepetitionTime'):
            exposure_info['repetition_time'] = str(dataset.RepetitionTime)
        
        # Extract echo time
        if hasattr(dataset, 'EchoTime'):
            exposure_info['echo_time'] = str(dataset.EchoTime)
        
        return exposure_info
    
    def _extract_location_info(self, dataset: pydicom.Dataset) -> Dict[str, Any]:
        """Extract location information"""
        location_info = {}
        
        # Extract institution name
        if hasattr(dataset, 'InstitutionName'):
            location_info['institution_name'] = str(dataset.InstitutionName)
        
        # Extract institution address
        if hasattr(dataset, 'InstitutionAddress'):
            location_info['institution_address'] = str(dataset.InstitutionAddress)
        
        # Extract department name
        if hasattr(dataset, 'InstitutionalDepartmentName'):
            location_info['department_name'] = str(dataset.InstitutionalDepartmentName)
        
        # Extract performing physician
        if hasattr(dataset, 'PerformingPhysicianName'):
            location_info['performing_physician'] = str(dataset.PerformingPhysicianName)
        
        # Extract reading physician
        if hasattr(dataset, 'PhysiciansOfRecord'):
            location_info['reading_physician'] = str(dataset.PhysiciansOfRecord)
        
        return location_info 