# PACS DICOM Study Validator - Flow Diagram

```mermaid
flowchart TD
    A[Client Upload] --> B[API Gateway]
    B --> C{Validate DICOM Format}

    C -->|Invalid| D[Return 400 Bad Request]
    C -->|Valid| E[Emit study.uploaded]

    E --> F[Validator Service]
    F --> G{Check Required Tags}

    G -->|Missing Tags| H[Emit validation.failed]
    G -->|All Tags Present| I[Emit validation.success]

    H --> J[Return 422 Unprocessable Entity]
    I --> K[Descriptor Service]

    K --> L[Extract Metadata]
    L --> M[Generate JSON]
    M --> N[Store Files]

    N --> O[Emit metadata.extracted]
    O --> P[Emit storage.completed]
    P --> Q[Emit study.processed]

    Q --> R[Return 200 Success]

    subgraph "API Gateway"
        B
        C
        E
        Q
        R
    end

    subgraph "Validator Service"
        F
        G
        H
        I
    end

    subgraph "Descriptor Service"
        K
        L
        M
        N
        O
        P
    end

    subgraph "Storage"
        S[studies/{study_id}/]
        T[original.dcm]
        U[metadata.json]
        V[validation.log]
    end

    N --> S
    S --> T
    S --> U
    S --> V

    style A fill:#e1f5fe
    style R fill:#c8e6c9
    style J fill:#ffcdd2
    style D fill:#ffcdd2
```

## Event Flow Sequence

```mermaid
sequenceDiagram
    participant Client
    participant APIGateway
    participant Validator
    participant Descriptor
    participant Storage

    Client->>APIGateway: POST /upload (DICOM file)
    APIGateway->>APIGateway: Validate DICOM format
    APIGateway->>APIGateway: Emit study.uploaded

    alt Valid DICOM
        APIGateway->>Validator: Send study for validation
        Validator->>Validator: Check required tags
        Validator->>APIGateway: Return validation result

        alt Valid Study
            APIGateway->>Descriptor: Send study for processing
            Descriptor->>Descriptor: Extract metadata
            Descriptor->>Descriptor: Generate JSON
            Descriptor->>Storage: Store files
            Descriptor->>APIGateway: Return processing result
            APIGateway->>Client: Return 200 Success
        else Invalid Study
            APIGateway->>Client: Return 422 Unprocessable Entity
        end
    else Invalid DICOM
        APIGateway->>Client: Return 400 Bad Request
    end
```

## Service Communication Flow

```mermaid
graph LR
    subgraph "External"
        A[Client]
    end

    subgraph "API Gateway"
        B[Upload Handler]
        C[Event Emitter]
        D[Response Handler]
    end

    subgraph "Validator Service"
        E[DICOM Validator]
        F[Tag Checker]
        G[Validation Emitter]
    end

    subgraph "Descriptor Service"
        H[Metadata Extractor]
        I[JSON Generator]
        J[Storage Handler]
        K[Processing Emitter]
    end

    subgraph "File System"
        L[studies/]
    end

    A --> B
    B --> C
    C --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> L

    C --> D
    G --> D
    K --> D
    D --> A

    style A fill:#e1f5fe
    style L fill:#fff3e0
```
