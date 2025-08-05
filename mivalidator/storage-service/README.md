# Storage Service

## Introduction

The Storage Service is responsible for archiving validated and described DICOM files and their associated metadata. It subscribes to the 'described' channel on Redis, moves the original DICOM file to a permanent archive location, saves the extracted metadata as a JSON file, and updates the study's status.

## Features

-   **File Archiving:** Moves original DICOM files from the uploads directory to a structured archive.
-   **Metadata Persistence:** Saves extracted DICOM metadata into a JSON file within the archive.
-   **Redis Integration:** Subscribes to the 'described' event to trigger archiving and updates study statuses.

## Setup

This service is designed to run within a Dockerized environment using `docker compose`. Ensure you have Docker and Docker Compose installed on your system.

### Dependencies

-   Redis
-   Status Service

### Environment Variables

The following environment variables are configured in the `compose.yaml` file:

-   `REDIS_URL`: URL for the Redis instance (e.g., `redis://redis:6379`)
-   `STATUS_SERVICE_URL`: URL for the Status Service (e.g., `http://status-service:8003`)
-   `UPLOADS_PATH`: Path to the temporary uploads directory (e.g., `/app/uploads`)
-   `ARCHIVE_PATH`: Path to the permanent archive directory (e.g., `/app/archive`)
-   `ENVIRONMENT`: Application environment (e.g., `production`)

## Running the Service

To run the Storage Service, navigate to the project root directory (`mivalidator/`) and use Docker Compose:

```bash
docker compose up --build -d storage-service
```

This command will build the `storage-service` image (if not already built or if changes are detected) and start the service along with its dependencies (`redis` and `status-service`).

## How it Works

1.  The service subscribes to the `described` channel on Redis.
2.  Upon receiving a message, it moves the DICOM file from the `uploads` directory to a study-specific subdirectory within the `archive` directory.
3.  It then saves the associated metadata as a `metadata.json` file in the same archive subdirectory.
4.  Finally, it updates the study's status to `archived` via the Status Service.
