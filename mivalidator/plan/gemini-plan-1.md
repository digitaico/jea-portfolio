# Revised Plan: A Decoupled, Event-Driven DICOM Validator

This plan refines the original proposal to build a truly decoupled, asynchronous, and testable system from the start, adhering to modern microservice best practices.

### Assessment of the Original Plan

**Strengths:**
*   **Clear Service Separation:** The division into API Gateway, Validator, and Descriptor services follows the Single Responsibility Principle.
*   **Event-Driven Mention:** The plan correctly identifies that an event-driven approach is suitable.
*   **Comprehensive Scope:** It considers essential aspects like configuration, error handling, and security.

**Areas for Improvement:**
1.  **Architectural Contradiction:** The original "Data Flow" described a synchronous, chained request model (`Gateway -> Validator -> Gateway -> Descriptor`), which creates tight coupling and contradicts the event-driven principle.
2.  **Vague Event System:** "Native event emitters" are not feasible for services running in separate containers. A concrete inter-service communication technology is required.
3.  **Removal of Testing:** The "no tests" approach is a critical flaw. A test-driven approach is essential for building reliable and maintainable microservices.
4.  **Dependency Contradiction:** The plan stated "no external dependencies" but correctly listed `pydicom` and `FastAPI`. This should be rephrased to "minimal essential dependencies."

---

### Proposed Build Plan & Refinements

We will build a system where services communicate asynchronously through a central message broker.

**1. Refined Architecture: A Pure Event-Driven Model**

*   **Communication Bus:** We will use **Redis Pub/Sub** as a lightweight, high-speed message broker. This replaces the ambiguous "custom event emitters" and the synchronous HTTP calls.
*   **Services (Revised Responsibilities):**
    *   **API Gateway:** Its *only* job is to accept an upload, save the file to a shared `uploads` volume, publish a `study.uploaded` event to a Redis channel, and immediately return a `202 Accepted` response with a `study_id`. It does not orchestrate or wait for validation.
    *   **Validator Service:** A standalone Python service that subscribes to the `study.uploaded` channel. When it receives an event, it validates the corresponding file from the `uploads` volume. It then publishes a `study.validated` or `study.validation.failed` event to another channel.
    *   **Descriptor Service:** A standalone Python service that subscribes to the `study.validated` channel. It processes the file, extracts metadata, and moves the final artifacts (the original file and the new `metadata.json`) to a persistent `archive` volume.

**2. What to Remove from the Original Plan**

*   **The "Data Flow" Section:** This is replaced entirely by the new event-driven flow.
*   **The "Lean Approach" of "No Tests":** This is replaced with a **Test-Driven Development (TDD)** approach.
*   **Direct Inter-service HTTP Communication:** All communication will be asynchronous via the Redis message bus.

**3. The Build Strategy (How to Build It)**

*   **Stage 1: Project Scaffolding & Containerization**
    1.  Create a root directory with a `docker-compose.yml`.
    2.  Define the three services (`api-gateway`, `validator-service`, `descriptor-service`) and a `redis` service within the `docker-compose.yml`.
    3.  Create separate directories (`/api-gateway`, `/validator-service`, `/descriptor-service`) for each service's source code.
    4.  Define two shared Docker volumes in the compose file: `uploads` (for temporary storage) and `archive` (for persistent storage).
    5.  Initialize a `requirements.txt` and a basic `config.json` for each service.

*   **Stage 2: Core Logic (Test-Driven Development)**
    1.  **Implement the Validator:**
        *   Write `pytest` unit tests to check the validation logic against sample valid and invalid DICOM files.
        *   Implement the validator's core logic to pass the tests.
        *   Implement the Redis subscriber logic to listen for `study.uploaded` events and the publisher logic to emit `study.validated` events.
    2.  **Implement the Descriptor:**
        *   Write `pytest` unit tests to verify that metadata is correctly extracted from a sample DICOM file.
        *   Implement the descriptor's core logic to pass the tests.
        *   Implement its Redis subscriber logic to listen for `study.validated` events.
    3.  **Implement the API Gateway:**
        *   Write `pytest` tests for the `/upload` endpoint to ensure it correctly saves a file and publishes an event to Redis.
        *   Implement the `FastAPI` application.

*   **Stage 3: Integration and End-to-End Validation**
    1.  Launch the entire stack using `docker-compose up --build`.
    2.  Use a simple script or `curl` to post a DICOM file to the gateway.
    3.  Observe the service logs (`docker-compose logs -f`) to trace the event flow.
    4.  Verify that the final DICOM file and its `metadata.json` appear correctly in the `archive` volume.
    5.  Test the failure path by uploading a corrupt file and ensuring it's handled gracefully without breaking the pipeline.

This revised plan establishes a robust, scalable, and professional architecture that truly embodies the principles of microservices and provides a solid foundation for future enhancements.
