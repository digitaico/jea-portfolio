"""
Shared Package for Healthcare Microservices
============================================

This package provides common utilities, database connections, NATS messaging,
event schemas, and repository patterns used across all healthcare microservices.

Modules:
--------
- database: Database connection, session management, and base models
- nats_client: NATS messaging client with pub/sub utilities
- events: Common event schemas and type definitions
- repositories: Repository pattern for data access layer
- utils: Common utilities for validation, logging, configuration

Usage:
------
    from shared import database, nats_client, events, repositories, utils

    # Initialize database
    await database.init_database()

    # Get database session
    async for db in database.get_db():
        # Use database session
        pass

    # Initialize NATS
    await nats_client.init_nats()

    # Publish event
    correlation_id = await nats_client.publish_domain_event(
        "appointment.scheduled",
        "appointment.scheduled",
        {"appointment_id": "123", "patient_id": "456"}
    )

    # Create repository
    repo_factory = repositories.RepositoryFactory(db)
    appointment_repo = repo_factory.get_appointment_repository()
"""

__version__ = "1.0.0"
__all__ = ["database", "nats_client", "events", "repositories", "utils"]