# API Gateway Service

## Introduction

The API Gateway service acts as the entry point for the DICOM validation system. It handles incoming requests, routes them to the appropriate backend services, and manages file uploads. It also interacts with Redis for status updates and event publishing.

## Features

-   **File Uploads:** Accepts DICOM file uploads.
-   **Request Routing:** Directs requests to the `validator-service`, `descriptor-service`, and `status-service`.
-   **Status Management:** Publishes and retrieves validation statuses via Redis.
-   **Health Checks:** Provides a health endpoint to monitor service status.

## Setup

This service is designed to run within a Dockerized environment using `docker compose`. Ensure you have Docker and Docker Compose installed on your system.

### Dependencies

-   Redis
-   Status Service
-   Validator Service
-   Descriptor Service

### Environment Variables

The following environment variables are configured in the `compose.yaml` file:

-   `REDIS_URL`: URL for the Redis instance (e.g., `redis://redis:6379`)
-   `ENVIRONMENT`: Application environment (e.g., `production`)

## Running the Service

To run the API Gateway service, navigate to the project root directory (`mivalidator/`) and use Docker Compose:

```bash
docker compose up --build -d api-gateway
```

This command will build the `api-gateway` image (if not already built or if changes are detected) and start the service along with its dependencies (`redis` and `status-service`).

## API Endpoints

-   **`/health` (GET):** Checks the health of the API Gateway service.
    -   Response: `{"status":"healthy", "service":"api-gateway"}`

-   **`/upload` (POST):** Handles DICOM file uploads. (Further details on request body and response will be added as the API evolves.)
