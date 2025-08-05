# PACS DICOM Study Validator - Project Tree

```
pacs-dicom-validator/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   └── config.json
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── app.py
│   │   ├── event_emitter.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── validator_client.py
│   │   │   └── descriptor_client.py
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── upload_handler.py
│   │   │   └── status_handler.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── study_data.py
│   │   │   └── event_data.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── logger.py
│   │       └── error_handler.py
│   └── logs/
│       └── .gitkeep
│
├── validator-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   └── config.json
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── app.py
│   │   ├── event_emitter.py
│   │   ├── validators/
│   │   │   ├── __init__.py
│   │   │   ├── dicom_validator.py
│   │   │   └── tag_checker.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── validation_result.py
│   │   │   └── event_data.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── logger.py
│   │       └── error_handler.py
│   └── logs/
│       └── .gitkeep
│
├── descriptor-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   └── config.json
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── app.py
│   │   ├── event_emitter.py
│   │   ├── extractors/
│   │   │   ├── __init__.py
│   │   │   └── metadata_extractor.py
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   └── json_generator.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── storage_handler.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── study_data.py
│   │   │   ├── metadata_schema.py
│   │   │   └── event_data.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── logger.py
│   │       └── error_handler.py
│   └── logs/
│       └── .gitkeep
│
├── shared/
│   ├── __init__.py
│   ├── constants/
│   │   ├── __init__.py
│   │   ├── dicom_tags.py
│   │   ├── events.py
│   │   └── error_codes.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── patient_info.py
│   │   ├── study_info.py
│   │   ├── modality_info.py
│   │   ├── exposure_info.py
│   │   ├── location_info.py
│   │   └── validation_info.py
│   └── utils/
│       ├── __init__.py
│       ├── event_emitter.py
│       ├── logger.py
│       └── error_handler.py
│
├── studies/
│   └── .gitkeep
│
├── docs/
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── postman_collection.json
│   ├── architecture/
│   │   ├── service-diagram.md
│   │   ├── data-flow.md
│   │   └── deployment-diagram.md
│   └── user-guide/
│       ├── installation.md
│       ├── configuration.md
│       └── api-reference.md
│
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   ├── health-check.sh
│   └── cleanup.sh
│
└── plan/
    ├── cursor-plan-1.md
    ├── mermaid-flow-diagram.md
    ├── class-diagram.md
    └── project-tree.md
```

## Configuration Files Structure

### API Gateway Config (`api-gateway/config/config.json`)

```json
{
  "service": {
    "name": "api-gateway",
    "port": 8000,
    "host": "0.0.0.0"
  },
  "services": {
    "validator": {
      "url": "http://validator-service:8001",
      "timeout": 30
    },
    "descriptor": {
      "url": "http://descriptor-service:8002",
      "timeout": 60
    }
  },
  "upload": {
    "max_file_size": 104857600,
    "allowed_extensions": [".dcm", ".dicom"],
    "temp_path": "/tmp"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/api-gateway.log"
  }
}
```

### Validator Service Config (`validator-service/config/config.json`)

```json
{
  "service": {
    "name": "validator-service",
    "port": 8001,
    "host": "0.0.0.0"
  },
  "validation": {
    "required_tags": {
      "patient_id": "(0010,0020)",
      "patient_name": "(0010,0010)",
      "study_date": "(0008,0020)",
      "study_time": "(0008,0030)",
      "modality": "(0008,0060)",
      "study_description": "(0008,1030)"
    },
    "validation_rules": {
      "max_file_size": 104857600,
      "check_integrity": true
    }
  },
  "logging": {
    "level": "INFO",
    "file": "logs/validator.log"
  }
}
```

### Descriptor Service Config (`descriptor-service/config/config.json`)

```json
{
  "service": {
    "name": "descriptor-service",
    "port": 8002,
    "host": "0.0.0.0"
  },
  "storage": {
    "studies_path": "/app/studies",
    "create_directories": true
  },
  "metadata": {
    "tag_mappings": {
      "patient": {
        "id": "(0010,0020)",
        "name": "(0010,0010)",
        "birth_date": "(0010,0030)",
        "sex": "(0010,0040)"
      },
      "study": {
        "id": "(0020,000D)",
        "date": "(0008,0020)",
        "time": "(0008,0030)",
        "description": "(0008,1030)"
      },
      "modality": {
        "type": "(0008,0060)",
        "manufacturer": "(0008,0070)",
        "model": "(0008,1090)"
      }
    }
  },
  "logging": {
    "level": "INFO",
    "file": "logs/descriptor.log"
  }
}
```

## Docker Configuration

### Docker Compose (`docker-compose.yml`)

```yaml
version: "3.8"

services:
  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    volumes:
      - ./studies:/app/studies
      - ./api-gateway/logs:/app/logs
    environment:
      - ENVIRONMENT=production
    depends_on:
      - validator-service
      - descriptor-service

  validator-service:
    build: ./validator-service
    ports:
      - "8001:8001"
    volumes:
      - ./validator-service/logs:/app/logs
    environment:
      - ENVIRONMENT=production

  descriptor-service:
    build: ./descriptor-service
    ports:
      - "8002:8002"
    volumes:
      - ./studies:/app/studies
      - ./descriptor-service/logs:/app/logs
    environment:
      - ENVIRONMENT=production
```

## File Storage Structure

### Studies Directory (`studies/`)

```
studies/
├── {study_id_1}/
│   ├── original.dcm
│   ├── metadata.json
│   └── validation.log
├── {study_id_2}/
│   ├── original.dcm
│   ├── metadata.json
│   └── validation.log
└── ...
```

### Metadata JSON Structure

```json
{
  "study_id": "1.2.826.0.1.3680043.8.498.123456789",
  "processing_time": "2024-01-15T10:30:00Z",
  "patient_info": {
    "patient_id": "12345",
    "patient_name": "DOE^JOHN",
    "patient_birth_date": "19800101",
    "patient_sex": "M"
  },
  "study_info": {
    "study_date": "20240115",
    "study_time": "103000",
    "study_description": "CHEST X-RAY",
    "accession_number": "ACC123456"
  },
  "modality_info": {
    "modality": "CR",
    "manufacturer": "SIEMENS",
    "model_name": "YSIO MAX",
    "station_name": "STATION1"
  },
  "exposure_info": {
    "exposure_time": "0.1",
    "exposure_mas": "2.5",
    "kvp": "120"
  },
  "location_info": {
    "institution_name": "GENERAL HOSPITAL",
    "department_name": "RADIOLOGY"
  },
  "validation_info": {
    "is_valid": true,
    "validation_time": "2024-01-15T10:30:05Z",
    "missing_tags": []
  }
}
```
