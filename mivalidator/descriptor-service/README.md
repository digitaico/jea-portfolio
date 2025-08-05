# Descriptor Service

## Introduction

The Descriptor Service is responsible for extracting metadata from validated DICOM files. It subscribes to the 'validation' channel on Redis, processes validated files, extracts relevant DICOM tags, and publishes a 'described' event with the extracted metadata.

## Features

-   **Metadata Extraction:** Extracts key information from DICOM files, categorizing it into patient, study, modality, exposure, and location details.
-   **Redis Integration:** Communicates with Redis for message queuing (subscribing to validation events, publishing described events) and status updates.

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

To run the Descriptor Service, navigate to the project root directory (`mivalidator/`) and use Docker Compose:

```bash
docker compose up --build -d descriptor-service
```

This command will build the `descriptor-service` image (if not already built or if changes are detected) and start the service along with its dependencies (`redis` and `status-service`).

## How it Works

1.  The service subscribes to the `validation` channel on Redis.
2.  Upon receiving a validated message, it updates the study's status to `processing`.
3.  It extracts metadata from the DICOM file using `pydicom`.
4.  Finally, it publishes a `described` event to Redis and updates the study's status to `described`.