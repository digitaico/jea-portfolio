# Status Service

## Introduction

The Status Service is a centralized component responsible for managing and providing real-time status updates for DICOM studies as they progress through the validation and processing pipeline. It uses Redis as its data store to maintain the current state of each study.

## Features

-   **Status Management:** Stores and retrieves the status of DICOM studies.
-   **Redis Integration:** Utilizes Redis for efficient storage and retrieval of study statuses.
-   **API Endpoints:** Provides RESTful API endpoints for updating and querying study statuses.
-   **Health Checks:** Offers a health endpoint to monitor service availability.

## Setup

This service is designed to run within a Dockerized environment using `docker compose`. Ensure you have Docker and Docker Compose installed on your system.

### Dependencies

-   Redis

### Environment Variables

The following environment variables are configured in the `compose.yaml` file:

-   `REDIS_URL`: URL for the Redis instance (e.g., `redis://redis:6379`)
-   `ENVIRONMENT`: Application environment (e.g., `production`)

## Running the Service

To run the Status Service, navigate to the project root directory (`mivalidator/`) and use Docker Compose:

```bash
docker compose up --build -d status-service
```

This command will build the `status-service` image (if not already built or if changes are detected) and start the service along with its dependency (`redis`).

## API Endpoints

-   **`/health` (GET):** Checks the health of the Status Service.
    -   Response: `{"status":"healthy", "service":"status-service"}`

-   **`/status/{study_id}` (GET):** Retrieves the current status of a specific study.

-   **`/status/{study_id}` (POST):** Updates the status of a specific study.
