# Project Tree - Python Learning Progression

## Complete Project Structure

```
learn-python/
├── 📁 **Core Files**
│   ├── main.py                    # v1 - Basic image transformations (Stage 1)
│   ├── main_v2.py                 # v2 - Database integration (Stage 3+)
│   ├── main_v3.py                 # v3 - Advanced features (Stage 4+)
│   ├── image_transformer.py       # Core image processing class
│   ├── calculator.py              # Basic OOP example
│   └── compare_versions.py        # Version comparison utility
│
├── 📁 **Database & Configuration**
│   ├── database.py                # PostgreSQL database management
│   ├── config.py                  # Configuration management
│   ├── env_manager.py             # Environment variable management
│   ├── env.example                # Environment variables template
│   └── init.sql                   # Database initialization script
│
├── 📁 **Advanced Features (v3+)**
│   ├── redis_manager.py           # Redis connection and management
│   ├── shopping_cart_api.py       # Redis shopping cart microservice
│   ├── redis_demo.py              # Redis functionality demonstration
│   └── stage6_realtime_features.py # Real-time features (SSE, WebSockets)
│
├── 📁 **API & Web Services**
│   ├── api.py                     # FastAPI main application
│   ├── stage6_client.html         # Web client for real-time features
│   └── server.js                  # Node.js server (if applicable)
│
├── 📁 **Documentation**
│   ├── README.md                  # Main project documentation
│   ├── VERSION_COMPARISON.md      # Version comparison table
│   ├── VERSION_FLOWCHART.md       # Mermaid flowcharts
│   ├── PROJECT_TREE.md            # This file
│   ├── ENVIRONMENT_GUIDE.md       # Environment setup guide
│   ├── REDIS_GUIDE.md             # Redis usage guide
│   └── plan/                      # Planning documents
│
├── 📁 **Docker & Deployment**
│   ├── docker-compose.yml         # Docker services configuration
│   ├── start_db.sh                # Database startup script
│   ├── start_redis.sh             # Redis startup script
│   └── scripts/                   # Deployment scripts
│
├── 📁 **Data & Storage**
│   ├── sources/                   # Source images
│   │   └── 1.jpg                  # Test image
│   ├── output/                    # Transformed images output
│   ├── uploads/                   # File uploads
│   └── logs/                      # Application logs
│
├── 📁 **Testing & Examples**
│   ├── enhanced_image_transformer.py # Enhanced image processing
│   ├── pillow_example.py          # Pillow library examples
│   ├── image_reading_comparison.py # Image reading comparison
│   └── tests/                     # Test files
│
├── 📁 **Utilities**
│   ├── cleanup_public_schema.py   # Database cleanup utility
│   ├── run_all_stages.py          # Stage runner utility
│   └── main_with_db.py            # Alternative database version
│
├── 📁 **Dependencies**
│   ├── requirements.txt           # Python dependencies
│   ├── pyproject.toml             # Project configuration
│   └── venv/                      # Virtual environment
│
└── 📁 **Archived & Legacy**
    └── archive/                   # Old versions and experiments
```

## Version-Specific File Organization

### Version 1 (Stage 1) - Basic Python & OOP

```
learn-python/
├── main.py                        # ✅ Main script v1
├── image_transformer.py           # ✅ Core image processing
├── calculator.py                  # ✅ Basic OOP example
├── sources/                       # ✅ Source images
│   └── 1.jpg
└── output/                        # ✅ Output directory
```

### Version 2 (Stage 3+) - Database Integration

```
learn-python/
├── main_v2.py                     # ✅ Main script v2
├── image_transformer.py           # ✅ Core image processing
├── database.py                    # ✅ Database management
├── config.py                      # ✅ Configuration management
├── env.example                    # ✅ Environment template
├── init.sql                       # ✅ Database schema
├── sources/                       # ✅ Source images
├── output/                        # ✅ Output directory
└── uploads/                       # ✅ File uploads
```

### Version 3 (Stage 4+) - Advanced Features

```
learn-python/
├── main_v3.py                     # ✅ Main script v3
├── image_transformer.py           # ✅ Core image processing
├── database.py                    # ✅ Database management
├── config.py                      # ✅ Configuration management
├── redis_manager.py               # ✅ Redis integration
├── shopping_cart_api.py           # ✅ Microservices
├── stage6_realtime_features.py    # ✅ Real-time features
├── api.py                         # ✅ FastAPI application
├── docker-compose.yml             # ✅ Docker services
├── sources/                       # ✅ Source images
├── output/                        # ✅ Output directory
├── uploads/                       # ✅ File uploads
└── logs/                          # ✅ Application logs
```

## File Descriptions

### Core Application Files

- **`main.py`**: Basic image transformations (v1) - standalone, no database
- **`main_v2.py`**: Database integration (v2) - stores transformation history
- **`main_v3.py`**: Advanced features (v3) - batch processing, configuration management
- **`image_transformer.py`**: Core image processing class with NumPy, OpenCV, and Pillow

### Database & Configuration

- **`database.py`**: PostgreSQL database management with SQLAlchemy
- **`config.py`**: Configuration management using Pydantic settings
- **`env_manager.py`**: Environment variable management utility
- **`init.sql`**: Database schema initialization

### Advanced Features

- **`redis_manager.py`**: Redis connection and shopping cart management
- **`shopping_cart_api.py`**: Redis-backed shopping cart microservice
- **`stage6_realtime_features.py`**: Real-time features with SSE and WebSockets

### Documentation

- **`README.md`**: Main project documentation and learning guide
- **`VERSION_COMPARISON.md`**: Detailed version comparison table
- **`VERSION_FLOWCHART.md`**: Mermaid flowcharts showing progression
- **`PROJECT_TREE.md`**: This comprehensive project structure

### Utilities & Tools

- **`compare_versions.py`**: Version comparison utility
- **`cleanup_public_schema.py`**: Database cleanup utility
- **`run_all_stages.py`**: Stage runner utility

## Key Directories

### `/sources`

- Contains test images for processing
- Used by all versions for input

### `/output`

- Stores transformed images
- Created automatically if not exists
- Used by all versions

### `/uploads`

- Stores uploaded files for API processing
- Used by v2+ versions

### `/logs`

- Application logs and debugging information
- Used by v3+ versions

### `/plan`

- Planning documents and architecture diagrams
- Learning progression documentation

## Technology Stack by Version

### Version 1 Stack

- Python 3.x
- NumPy
- OpenCV (cv2)
- Pillow (PIL)

### Version 2 Stack

- All v1 technologies
- PostgreSQL
- SQLAlchemy
- FastAPI
- python-dotenv

### Version 3 Stack

- All v2 technologies
- Redis
- Docker
- Microservices architecture
- Advanced CLI (argparse)

## Learning Progression Path

1. **Start with v1**: Understand basic Python concepts and OOP
2. **Move to v2**: Learn database integration and persistence
3. **Use v3**: Production-ready features and advanced capabilities

Each version builds upon the previous while preserving all functionality for learning review.
