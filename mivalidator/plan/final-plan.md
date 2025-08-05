# Final Plan: Hybrid DICOM Validator

This document presents a final, unified plan that combines the detailed specifications of the initial plan with the robust, decoupled architecture of the revised plan. It provides a comprehensive blueprint for building a scalable, testable, and maintainable DICOM validation system.

## 1. Core Architecture: Asynchronous & Event-Driven

The system will be built on a pure event-driven architecture. Services are fully decoupled and communicate asynchronously using **Redis Pub/Sub** as a lightweight message broker. This eliminates synchronous dependencies and allows for independent scaling and development of each component.

- **Architectural Pattern**: Microservices
- **Communication**: Event-Driven (Redis Pub/Sub)
- **Development Methodology**: Test-Driven Development (TDD)
- **Deployment**: Containerized (Docker)

## 2. Services Architecture

The system consists of four distinct services and a central message broker.

### a. API Gateway Service

- **Purpose**: The single entry point for all client interactions. It handles initial intake and provides status feedback without participating in the core logic.
- **Responsibilities**:
    - Accept DICOM study uploads (`multipart/form-data`) via a `POST /upload` endpoint.
    - Immediately save the raw study to a shared `uploads` volume.
    - Generate a unique `study_id` for tracking.
    - Publish a `study.uploaded` event to the Redis `uploads` channel with the `study_id` and file path.
    - Respond immediately to the client with `202 Accepted` and the `study_id`.
    - Provide a `GET /status/{study_id}` endpoint to query the study's processing state from the Status Service.

### b. Validator Service

- **Purpose**: A background worker dedicated to validating the structural and technical integrity of DICOM studies.
- **Responsibilities**:
    - Subscribe to the `study.uploaded` event channel.
    - Upon receiving an event, retrieve the corresponding study from the `uploads` volume.
    - Perform validation checks (valid DICOM format, required tags present, no corruption).
    - Publish the result as either a `study.validated` or `study.validation.failed` event. The event payload will include the `study_id` and validation details (e.g., error messages).
    - Update the study's status via the Status Service.

### c. Descriptor Service

- **Purpose**: A background worker that extracts metadata from validated studies and prepares the final archive.
- **Responsibilities**:
    - Subscribe to the `study.validated` event channel.
    - Retrieve the validated study from the `uploads` volume.
    - Parse the DICOM file and extract key metadata into a structured `metadata.json` file.
    - Create a final, organized directory for the study in the `archive` volume.
    - Move the original study and the new `metadata.json` into the final directory.
    - Publish a `study.archived` event.
    - Update the study's status via the Status Service.

### d. Status Service

- **Purpose**: To track and report the processing status of each study.
- **Responsibilities**:
    - Provide an internal API for other services to post status updates (e.g., `POST /status/{study_id}` with a JSON body like `{"status": "validating"}`).
    - Store the latest status for each `study_id` in Redis (using simple key-value pairs).
    - Expose this status information to the API Gateway to fulfill client requests.

## 3. Event & Data Flow

1.  **Upload**: A client `POST`s a DICOM file to the **API Gateway**.
2.  **Intake**: The Gateway saves the file to the `uploads` volume and publishes a `study.uploaded` event to Redis. It immediately returns `202 Accepted` to the client.
3.  **Validation**: The **Validator Service** consumes the event, validates the file, and publishes `study.validated` or `study.validation.failed`. It also updates the status to "validated" or "failed".
4.  **Metadata Extraction**: The **Descriptor Service** consumes the `study.validated` event. It processes the file, generates `metadata.json`, and moves the artifacts to the `archive` volume.
5.  **Completion**: The Descriptor Service updates the status to "archived".
6.  **Status Check**: The client can periodically poll the `GET /status/{study_id}` endpoint on the Gateway to get the latest status.

## 4. Final File Structure (in `archive` volume)

```
/archive/{study_id}/
├── original.dcm
└── metadata.json
```

## 5. Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **DICOM Processing**: pydicom
- **Event Bus**: Redis
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest

## 6. Non-Functional Requirements

The detailed considerations from the initial plan will be fully implemented:

- **Configuration**: Each service will have a `config.json` for ports, paths, and other settings.
- **Error Handling**:
    - **API Gateway**: Returns standard HTTP error codes (`400`, `422`, `500`).
    - **Internal Services**: Handle errors gracefully and publish failure events (e.g., `study.validation.failed`).
- **Security**: Implement file size limits, type validation, and path traversal prevention.
- **Performance**: Leverage asynchronous I/O, memory-efficient parsing, and the non-blocking nature of the event-driven design.
- **Monitoring**: Each service will log key events, processing times, and error rates to standard output for aggregation by container orchestration tools.
