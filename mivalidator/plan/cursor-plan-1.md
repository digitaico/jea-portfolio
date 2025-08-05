# PACS DICOM Study Validator - MVP Plan

## Overview

A microservices-based system that validates PACS DICOM studies, extracts metadata, and stores valid studies with their metadata in JSON format.

## Architecture Principles

- **Event-Driven Architecture**: Using native event emitters
- **Microservices Pattern**: Three independent services
- **Single Responsibility**: Each service has one clear purpose
- **Lean Approach**: Minimal code, no tests, no external dependencies
- **Read-Only Operations**: No file/folder modifications, only storage

## Services Architecture

### 1. API Gateway Service

**Purpose**: Entry point for DICOM study uploads and response handling

**Responsibilities**:

- Accept DICOM study uploads (multipart/form-data)
- Route requests to validator service
- Handle responses and return appropriate HTTP status codes
- Emit events for study processing lifecycle

**Endpoints**:

- `POST /upload` - Upload DICOM study
- `GET /status/{study_id}` - Get processing status

**Event Emissions**:

- `study.uploaded` - When study is received
- `study.validated` - When validation completes
- `study.processed` - When processing completes

### 2. Validator Service

**Purpose**: Validate DICOM study integrity and basic structure

**Responsibilities**:

- Validate DICOM file format and structure
- Check for required DICOM tags
- Verify study completeness
- Emit validation events

**Validation Criteria**:

- Valid DICOM format
- Required tags present (Patient ID, Study Date, Modality, etc.)
- No corrupted data
- Valid study structure

**Event Emissions**:

- `validation.success` - Study is valid
- `validation.failed` - Study is invalid

### 3. Descriptor Service

**Purpose**: Extract metadata from valid DICOM studies

**Responsibilities**:

- Parse DICOM tags and extract metadata
- Generate structured JSON output
- Store study and metadata in `studies` folder
- Emit processing completion events

**Extracted Metadata**:

- Patient information (ID, name, birth date)
- Study information (ID, date, time, description)
- Modality and equipment details
- Exposure parameters (time, repetitions, technique)
- Location and institution data
- Series and image information

**Event Emissions**:

- `metadata.extracted` - Metadata extraction completed
- `storage.completed` - Files stored successfully

## Data Flow

1. **Upload**: Client uploads DICOM study to API Gateway
2. **Validation**: API Gateway sends study to Validator Service
3. **Validation Result**: Validator returns validation status
4. **Metadata Extraction**: If valid, API Gateway sends to Descriptor Service
5. **Storage**: Descriptor Service stores study and metadata
6. **Response**: API Gateway returns final result to client

## Event Flow

```
study.uploaded → validation.request → validation.result →
metadata.extraction → storage.completion → study.processed
```

## File Structure

```
studies/
├── {study_id}/
│   ├── original.dcm          # Original DICOM file
│   ├── metadata.json         # Extracted metadata
│   └── validation.log        # Validation details
```

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI (API Gateway)
- **DICOM Processing**: pydicom
- **Event System**: Python asyncio + custom event emitters
- **File Storage**: Local filesystem
- **JSON Processing**: Standard library json

## Configuration

Each service will have a `config.json` file:

- Service ports and endpoints
- File storage paths
- Event emitter configurations
- DICOM tag mappings

## Error Handling

- Invalid DICOM format → 400 Bad Request
- Missing required tags → 422 Unprocessable Entity
- Processing errors → 500 Internal Server Error
- Storage failures → 503 Service Unavailable

## Security Considerations

- File size limits for uploads
- DICOM file type validation
- Path traversal prevention
- Input sanitization

## Performance Considerations

- Asynchronous processing
- Non-blocking I/O operations
- Memory-efficient DICOM parsing
- Event-driven communication

## Monitoring

- Event emission logging
- Processing time metrics
- Error rate tracking
- Storage usage monitoring

## Deployment

- Each service as independent container
- Shared volume for studies folder
- Environment-based configuration
- Health check endpoints
