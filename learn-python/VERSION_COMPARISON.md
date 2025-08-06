# Version Comparison - Main Scripts

## Overview

This document provides a comprehensive comparison of the different versions of the main script, showing the learning progression from basic Python concepts to advanced microservices architecture.

## Version History

| Version | File         | Stage    | Description          | Status      |
| ------- | ------------ | -------- | -------------------- | ----------- |
| v1      | `main.py`    | Stage 1  | Basic Python & OOP   | ✅ Complete |
| v2      | `main_v2.py` | Stage 3+ | Database Integration | ✅ Complete |
| v3      | `main_v3.py` | Stage 4+ | Advanced Features    | ✅ Complete |

## Detailed Feature Comparison

| Feature                  | v1 (main.py) | v2 (main_v2.py) | v3 (main_v3.py) |
| ------------------------ | ------------ | --------------- | --------------- |
| **Core Functionality**   |
| Image transformations    | ✅           | ✅              | ✅              |
| File system operations   | ✅           | ✅              | ✅              |
| Command-line interface   | ✅           | ✅              | ✅              |
| **Database Integration** |
| Database storage         | ❌           | ✅              | ✅              |
| Transformation history   | ❌           | ✅              | ✅              |
| Progress tracking        | ❌           | ✅              | ✅              |
| **Error Handling**       |
| Basic error handling     | ❌           | ✅              | ✅              |
| Database error handling  | ❌           | ✅              | ✅              |
| Comprehensive logging    | ❌           | ❌              | ✅              |
| **Configuration**        |
| Hardcoded values         | ✅           | ❌              | ❌              |
| Environment variables    | ❌           | ✅              | ✅              |
| JSON config files        | ❌           | ❌              | ✅              |
| **Advanced Features**    |
| Batch processing         | ❌           | ❌              | ✅              |
| Performance monitoring   | ❌           | ❌              | ✅              |
| Command-line arguments   | Basic        | Basic           | Advanced        |
| **Data Management**      |
| Single image processing  | ✅           | ✅              | ✅              |
| Batch image processing   | ❌           | ❌              | ✅              |
| Configuration management | ❌           | ❌              | ✅              |

## Technical Details

### v1: Basic Python & OOP (Stage 1)

- **Purpose**: Learn basic Python concepts and OOP
- **Key Files**: `main.py`, `image_transformer.py`
- **Features**:
  - Image transformations using NumPy and OpenCV
  - File system operations
  - Command-line interface
  - No database storage
  - No progress tracking

### v2: Database Integration (Stage 3+)

- **Purpose**: Add database integration and persistence
- **Key Files**: `main_v2.py`, `database.py`, `config.py`
- **Features**:
  - All v1 features
  - PostgreSQL database integration
  - SQLAlchemy ORM
  - Transformation history tracking
  - Progress monitoring
  - Environment variable configuration

### v3: Advanced Features (Stage 4+)

- **Purpose**: Add production-ready features and advanced capabilities
- **Key Files**: `main_v3.py`, `redis_manager.py`, `shopping_cart_api.py`
- **Features**:
  - All v2 features
  - Batch processing capabilities
  - Enhanced error handling
  - Performance monitoring
  - Configuration management
  - Advanced command-line interface
  - Redis integration
  - Microservices architecture

## Usage Examples

### v1 - Basic Usage

```bash
python3 main.py [image_path]
python3 main.py sources/1.jpg
```

### v2 - Database Integration

```bash
python3 main_v2.py [image_path]
python3 main_v2.py sources/1.jpg
```

### v3 - Advanced Features

```bash
python3 main_v3.py [image_path] [--batch] [--config config.json]
python3 main_v3.py sources/1.jpg --batch
python3 main_v3.py --list-transformations
```

## Learning Progression

1. **v1 → v2**: Added database integration

   - PostgreSQL with SQLAlchemy
   - Transformation history tracking
   - Environment variable configuration
   - Error handling improvements

2. **v2 → v3**: Added advanced features
   - Batch processing capabilities
   - Enhanced error handling and logging
   - Configuration management
   - Performance monitoring
   - Advanced command-line interface

## Database Schema

All versions v2+ use the `image_processor` schema with the following table:

```sql
CREATE TABLE image_processor.transformation_history (
    id BIGSERIAL PRIMARY KEY,
    image_path VARCHAR NOT NULL,
    transformation_type VARCHAR NOT NULL,
    parameters JSONB,
    output_path VARCHAR,
    processing_time INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## File Structure

```
learn-python/
├── main.py              # v1 - Basic functionality
├── main_v2.py           # v2 - Database integration
├── main_v3.py           # v3 - Advanced features
├── image_transformer.py # Core image processing class
├── database.py          # Database management (v2+)
├── config.py            # Configuration management (v2+)
├── redis_manager.py     # Redis integration (v3+)
├── shopping_cart_api.py # Microservices example (v3+)
└── compare_versions.py  # Version comparison utility
```

## Recommendations

- **Start with v1**: Understand basic Python concepts and OOP
- **Move to v2**: Learn database integration and persistence
- **Use v3**: Production-ready features and advanced capabilities

Each version is preserved independently for learning review and comparison.
