# Validator Service

## Introduction

The Validator Service is responsible for validating uploaded DICOM files. It subscribes to an 'uploads' channel on Redis, processes incoming file paths, performs DICOM validation, and publishes the validation results to a 'validation' channel.

## Features

-   **DICOM Validation:** Validates DICOM files for integrity and adherence to specified standards (e.g., presence of required tags).
-   **Redis Integration:** Communicates with Redis for message queuing (subscribing to uploads, publishing validation results) and status updates.
-   **Error Handling:** Gracefully handles invalid DICOM files and other processing errors.

## Setup

This service is designed to run within a Dockerized environment using `docker compose`. Ensure you have Docker and Docker Compose installed on your system.

### Dependencies

-   Redis
-   Status Service

### Environment Variables

The following environment variables are configured in the `compose.yaml` file:

-   `REDIS_URL`: URL for the Redis instance (e.g., `redis://redis:6379`)
-   `STATUS_SERVICE_URL`: URL for the Status Service (e.g., `http://status-service:8003`)
-   `ENVIRONMENT`: Application environment (e.g., `production`)

## Running the Service

To run the Validator Service, navigate to the project root directory (`mivalidator/`) and use Docker Compose:

```bash
docker compose up --build -d validator-service
```

This command will build the `validator-service` image (if not already built or if changes are detected) and start the service along with its dependencies (`redis` and `status-service`).

## How it Works

1.  The service subscribes to the `uploads` channel on Redis.
2.  When a new message (containing `study_id` and `file_path`) is received, it updates the study's status to `validating`.
3.  It then attempts to validate the DICOM file using `pydicom`.
4.  Based on the validation result, it publishes a `validation` event to Redis and updates the study's status to `validated` or `validation_failed`.
