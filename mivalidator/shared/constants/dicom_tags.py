# DICOM tags constants

# Required tags for validation
REQUIRED_TAGS = {
    "patient_id": "(0010,0020)",
    "patient_name": "(0010,0010)",
    "study_date": "(0008,0020)",
    "study_time": "(0008,0030)",
    "modality": "(0008,0060)",
    "study_description": "SeriesDescription",
    "study_instance_uid": "(0020,000D)",
    "accession_number": "(0008,0050)"
}

# Metadata extraction tags
METADATA_TAGS = {
    "patient": {
        "id": "(0010,0020)",
        "name": "(0010,0010)",
        "birth_date": "(0010,0030)",
        "sex": "(0010,0040)",
        "age": "(0010,1010)"
    },
    "study": {
        "id": "(0020,000D)",
        "date": "(0008,0020)",
        "time": "(0008,0030)",
        "description": "(0008,1030)",
        "accession_number": "(0008,0050)",
        "study_id": "(0020,0010)"
    },
    "modality": {
        "type": "(0008,0060)",
        "manufacturer": "(0008,0070)",
        "model": "(0008,1090)",
        "station_name": "(0008,1010)"
    },
    "exposure": {
        "exposure_time": "(0018,1150)",
        "exposure_mas": "(0018,1152)",
        "kvp": "(0018,0060)",
        "repetition_time": "(0018,0080)",
        "echo_time": "(0018,0081)"
    },
    "location": {
        "institution_name": "(0008,0080)",
        "institution_address": "(0008,0081)",
        "department_name": "(0008,1040)",
        "performing_physician": "(0008,1050)",
        "reading_physician": "(0008,1060)"
    }
} 