# Shared Package Documentation

## Overview

The `shared/` package provides common utilities, database connections, NATS messaging, event schemas, and repository patterns used across all healthcare microservices.

## Architecture

```
shared/
├── __init__.py          # Package initialization and documentation
├── database.py          # Database connection, session management, base models
├── nats_client.py       # NATS messaging client with pub/sub utilities
├── events.py            # Common event schemas and type definitions
├── repositories.py      # Repository pattern for data access layer
├── utils.py             # Common utilities (validation, logging, config)
└── README.md           # This documentation
```

## Quick Start

### 1. Import Shared Modules

```python
from shared import database, nats_client, events, repositories, utils
```

### 2. Initialize Services

```python
# Initialize database
await database.init_database()

# Initialize NATS
await nats_client.init_nats()
```

### 3. Use Database Session

```python
from shared.database import get_db

async for db in get_db():
    # Use database session
    repo_factory = repositories.RepositoryFactory(db)
    appointment_repo = repo_factory.get_appointment_repository()
```

### 4. Publish Events

```python
from shared import nats_client, events

# Create and publish event
appointment_event = events.AppointmentScheduledEvent(
    appointment_id="123",
    patient_id="456",
    doctor_id="789",
    appointment_time=datetime.utcnow(),
    duration_minutes=30
)

correlation_id = await nats_client.publish_event(
    "appointment.scheduled",
    appointment_event.model_dump()
)
```

### 5. Subscribe to Events

```python
from shared.nats_client import nats_client

async def handle_appointment_event(msg):
    """Handle incoming appointment events"""
    event_data = json.loads(msg.data.decode())
    event = events.create_appointment_event(event_data["event_type"], event_data)
    print(f"Received: {event.event_type}")

# Subscribe to appointment events
await nats_client.subscribe("appointment.*", handle_appointment_event)
```

## Module Details

### Database Module (`database.py`)

Provides database connection management and base models:

```python
from shared.database import get_db, init_database, BaseModel

# Initialize database
await init_database()

# Use in FastAPI routes
async for db in get_db():
    # Database operations here
    pass
```

### NATS Client Module (`nats_client.py`)

Handles NATS messaging with clean pub/sub interface:

```python
from shared.nats_client import nats_client, publish_domain_event

# Publish domain event
correlation_id = await publish_domain_event(
    "appointment.scheduled",
    "appointment.scheduled",
    {"appointment_id": "123"}
)

# Subscribe to events
await nats_client.subscribe("appointment.*", callback_function)
```

### Events Module (`events.py`)

Centralized event schemas and utilities:

```python
from shared.events import AppointmentScheduledEvent, EventSubjects

# Create typed event
event = AppointmentScheduledEvent(
    appointment_id="123",
    patient_id="456",
    doctor_id="789",
    appointment_time=datetime.utcnow(),
    duration_minutes=30
)

# Use subject constants
subject = EventSubjects.APPOINTMENT_SCHEDULED
```

### Repositories Module (`repositories.py`)

Repository pattern for data access:

```python
from shared.repositories import RepositoryFactory

# Create repository factory
repo_factory = RepositoryFactory(db)

# Get specific repository
appointment_repo = repo_factory.get_appointment_repository()

# Use repository methods
appointment = await appointment_repo.get_by_id("123")
```

### Utils Module (`utils.py`)

Common utilities and configuration:

```python
from shared.utils import Config, ValidationUtils, TimeUtils, IDGenerator

# Use configuration
db_url = Config.DATABASE_URL

# Generate IDs
appointment_id = IDGenerator.generate_uuid()

# Validate data
is_valid = ValidationUtils.is_valid_email("user@example.com")

# Time utilities
now = TimeUtils.now_utc()
```

## Best Practices

### 1. Always Use Dependency Injection

```python
from fastapi import Depends
from shared.database import get_db

@app.get("/appointments")
async def get_appointments(db = Depends(get_db)):
    # Use db session
    pass
```

### 2. Handle Exceptions Properly

```python
from shared.utils import LoggingUtils

try:
    # Your code here
    pass
except Exception as e:
    logger.error(LoggingUtils.format_error_log(e, "Appointment creation failed"))
```

### 3. Use Event Correlation IDs

```python
correlation_id = await nats_client.publish_event(subject, event_data)
# Store correlation_id for tracking distributed transactions
```

### 4. Validate Events

```python
from shared.events import validate_event_data

if validate_event_data(event):
    # Process event
    pass
else:
    logger.error("Invalid event data received")
```

## Migration Guide

### From Old Coupled Code

**Old (coupled):**
```python
# Direct database operations in handlers
@app.post("/appointments")
async def create_appointment():
    # Database code mixed with business logic
    conn = await get_connection()
    await conn.execute("INSERT INTO appointments...")
```

**New (modular):**
```python
# Clean separation using shared modules
@app.post("/appointments")
async def create_appointment(db = Depends(get_db)):
    repo_factory = repositories.RepositoryFactory(db)
    appointment_repo = repo_factory.get_appointment_repository()

    appointment = await appointment_repo.create(**appointment_data)

    # Publish event using shared NATS client
    await nats_client.publish_domain_event(
        events.EventSubjects.APPOINTMENT_SCHEDULED,
        "appointment.scheduled",
        appointment.__dict__
    )
```

## Testing

The shared modules are designed to be easily testable:

```python
import pytest
from shared.database import get_db
from shared.nats_client import NATSClient

async def test_appointment_creation():
    # Mock database session
    async for db in get_db():
        # Test repository methods
        pass

    # Mock NATS client
    nats_client = NATSClient()
    # Test event publishing
    pass
```

## Contributing

When adding new shared functionality:

1. **Add to appropriate module** - Don't create new modules unless necessary
2. **Update documentation** - Keep this README current
3. **Add type hints** - All functions should have proper type annotations
4. **Write tests** - Ensure new functionality is tested
5. **Update imports** - Add to `__init__.py` if exporting new functionality

## Version History

- **1.0.0**: Initial release with database, NATS, events, repositories, and utils modules