# Event constants for the DICOM validator system

# Event types
STUDY_UPLOADED = "study.uploaded"
STUDY_VALIDATED = "study.validated"
STUDY_VALIDATION_FAILED = "study.validation.failed"
STUDY_ARCHIVED = "study.archived"
STUDY_PROCESSING_FAILED = "study.processing.failed"

# Status constants
STATUS_UPLOADED = "uploaded"
STATUS_VALIDATING = "validating"
STATUS_VALIDATED = "validated"
STATUS_VALIDATION_FAILED = "validation_failed"
STATUS_PROCESSING = "processing"
STATUS_ARCHIVED = "archived"
STATUS_FAILED = "failed"

# Redis channels
UPLOADS_CHANNEL = "uploads"
VALIDATION_CHANNEL = "validation"
ARCHIVE_CHANNEL = "archive" 