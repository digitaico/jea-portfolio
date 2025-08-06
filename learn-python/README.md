# Python Learning Path - Image Processor API

A comprehensive Python learning project that evolves from simple image transformations to a full FastAPI microservice with PostgreSQL 16 database integration and Redis-powered shopping cart.

## 🎯 Learning Progression

This project demonstrates a **step-by-step progression** from basic Python concepts to advanced microservices architecture:

### 📊 **Stage 1: Basic Python & OOP** ✅

- **`image_transformer.py`** - Core image processing class
  - NumPy array manipulation
  - OpenCV image transformations
  - Pillow image processing
  - Error handling and validation
- **`main.py`** - CLI interface (v1 - Basic)
  - Command-line argument processing
  - File system operations
  - User interaction
  - **No database storage**
- **`main_v2.py`** - Database integration (v2 - Stage 3+)
  - All v1 features plus database storage
  - Transformation history tracking
  - Progress monitoring
- **`main_v3.py`** - Advanced features (v3 - Stage 4+)
  - All v2 features plus advanced capabilities
  - Batch processing
  - Enhanced error handling
  - Configuration management
  - Performance monitoring
- **`calculator.py`** - Basic OOP example
  - Class definition and methods
  - Inheritance and polymorphism

### 📊 **Stage 2: Advanced Image Processing**

_Enhanced functionality with multiple libraries_

- **`enhanced_image_transformer.py`** - Extended image processing capabilities
- **`pillow_example.py`** - Pillow library demonstrations
- **`image_reading_comparison.py`** - Comparing different image processing approaches

**Learning Focus:**

- Multiple library integration (OpenCV + Pillow)
- Performance optimization
- Image format handling
- Advanced transformations

### 📊 **Stage 3: Web API Development**

_FastAPI application with database integration_

- **`api.py`** - FastAPI application for image processing
- **`config.py`** - Configuration management with Pydantic
- **`database.py`** - PostgreSQL integration with SQLAlchemy
- **`env_manager.py`** - Environment variable management

**Learning Focus:**

- FastAPI framework
- REST API design
- Database integration (PostgreSQL 16)
- Environment configuration
- Async programming

### 📊 **Stage 4: Advanced Features**

_Redis integration, shopping cart, and microservices_

- **`redis_manager.py`** - Redis connection and shopping cart management
- **`shopping_cart_api.py`** - Separate FastAPI service for shopping cart
- **`redis_demo.py`** - Redis functionality demonstrations

**Learning Focus:**

- Redis caching and data structures
- Microservices architecture
- Session management
- Service communication

### 📊 **Stage 5: Production Ready**

_Docker, monitoring, and deployment_

- **`docker-compose.yml`** - Multi-service container orchestration
- **`start_db.sh`** / **`start_redis.sh`** - Service startup scripts
- **`init.sql`** - Database initialization
- **`cleanup_public_schema.py`** - Database maintenance

**Learning Focus:**

- Containerization with Docker
- Service orchestration
- Database schema management
- Production deployment

### 📊 **Stage 6: Real-Time Features** ✅

- **`stage6_realtime_features.py`** - Real-time processing API
  - Server-Sent Events (SSE) for progress streaming
  - WebSocket connections for live updates
  - Redis pub/sub integration
  - Background processing with progress tracking
  - Real-time notifications
- **`stage6_client.html`** - Interactive web client
  - Real-time progress visualization
  - WebSocket connection management
  - Event logging and monitoring
  - Active transformation tracking

**Learning Focus:**

- Real-time communication patterns
- Event-driven architecture
- WebSocket and SSE implementation
- Background task processing
- Progress tracking and monitoring

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone or navigate to the project
cd learn-python

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env
# Edit .env with your database credentials
```

### 2. Database Setup

```bash
# Start PostgreSQL 16 using Docker
./start_db.sh

# Or manually with Docker Compose
docker-compose up -d postgres
```

### 3. Redis Setup

```bash
# Start Redis using Docker
./start_redis.sh

# Or manually with Docker Compose
docker-compose up -d redis redis-commander
```

### 4. Test Environment Variables

```bash
# Test environment configuration
python env_manager.py
```

### 5. Start the APIs

```bash
# Start Image Processing API
python api.py

# Start Shopping Cart API (in another terminal)
python shopping_cart_api.py

# Or with uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
uvicorn shopping_cart_api:app --host 0.0.0.0 --port 8001 --reload
```

### 6. Access the APIs

- **Image Processing API**: http://localhost:8000/docs
- **Shopping Cart API**: http://localhost:8001/docs
- **Redis Commander**: http://localhost:8081
- **pgAdmin**: http://localhost:5050

## 📁 Project Structure

```
learn-python/
├── # Stage 1: Basic Python & OOP
│   ├── image_transformer.py      # Core image processing class
│   ├── main.py                   # CLI demo script
│   └── calculator.py             # Basic calculator example
│
├── # Stage 2: Advanced Image Processing
│   ├── enhanced_image_transformer.py  # Extended functionality
│   ├── pillow_example.py             # Pillow demonstrations
│   └── image_reading_comparison.py   # Library comparisons
│
├── # Stage 3: Web API Development
│   ├── api.py                    # FastAPI application (Image Processing)
│   ├── config.py                 # Configuration management
│   ├── database.py               # Database models and connection
│   └── env_manager.py            # Environment variable utilities
│
├── # Stage 4: Advanced Features
│   ├── shopping_cart_api.py      # FastAPI application (Shopping Cart)
│   ├── redis_manager.py          # Redis shopping cart manager
│   └── redis_demo.py             # Redis functionality demo
│
├── # Stage 5: Production Ready
│   ├── docker-compose.yml        # Multi-service orchestration
│   ├── start_db.sh               # Database startup script
│   ├── start_redis.sh            # Redis startup script
│   ├── init.sql                  # Database initialization
│   └── cleanup_public_schema.py  # Database maintenance
│
├── # Configuration & Dependencies
│   ├── requirements.txt          # Python dependencies
│   ├── env.example               # Environment template
│   ├── .env                      # Environment variables
│   └── README.md                 # This file
│
├── # Data Directories
│   ├── uploads/                  # Uploaded images
│   └── output/                   # Transformed images
│
└── # Documentation
    ├── ENVIRONMENT_GUIDE.md      # Environment management guide
    └── REDIS_GUIDE.md            # Redis usage guide
```

## 🎯 Learning Objectives

This project covers:

- **Object-Oriented Programming** - Classes, methods, inheritance
- **Image Processing** - OpenCV, Pillow, NumPy
- **Web APIs** - FastAPI, async programming
- **Database Integration** - PostgreSQL 16, SQLAlchemy
- **Caching & Sessions** - Redis, shopping cart, session management
- **Environment Management** - python-dotenv, configuration
- **Docker** - Containerization, Docker Compose
- **Modern Python** - Type hints, async/await, Pydantic

## 🔧 Environment Variables

### Core Configuration

Create a `.env` file based on `env.example`:

```bash
# Database Configuration (PostgreSQL 16)
DATABASE_URL=postgresql://username:password@localhost:5432/image_processor
DB_HOST=localhost
DB_PORT=5432
DB_NAME=image_processor
DB_USER=postgres
DB_PASSWORD=password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_URL=redis://localhost:6379/0

# Application Configuration
APP_NAME=Image Processor API
DEBUG=True
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=uploads
OUTPUT_DIR=output
MAX_FILE_SIZE=10485760  # 10MB

# Optional: Redis Commander
REDIS_COMMANDER_USER=admin
REDIS_COMMANDER_PASSWORD=admin
```

## 🗄️ Database (PostgreSQL 16)

### PostgreSQL 16 Features

- **Improved Performance**: Up to 25% faster query execution
- **Better Parallelism**: Enhanced parallel query processing
- **Logical Replication**: Improved logical replication capabilities
- **JSON/JSONB**: Enhanced JSON processing and indexing
- **Security**: Latest security patches and features
- **Monitoring**: Better monitoring and observability

### Database Schema

The project uses a dedicated `image_processor` schema to avoid conflicts with existing data:

```sql
-- Create dedicated schema
CREATE SCHEMA IF NOT EXISTS image_processor;

-- Transformation history table
CREATE TABLE image_processor.transformation_history (
    id INTEGER PRIMARY KEY,
    image_path VARCHAR NOT NULL,
    transformation_type VARCHAR NOT NULL,
    parameters JSON,
    output_path VARCHAR,
    processing_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Index for better performance
CREATE INDEX ix_transformation_history_id
ON image_processor.transformation_history (id);
```

### Database Setup

The project uses PostgreSQL 16 with Docker:

```bash
# Start database
docker-compose up -d postgres

# Check status
docker-compose ps

# View logs
docker-compose logs postgres

# Stop database
docker-compose down
```

## 🎯 API Endpoints

### Image Processing API (Port 8000)

- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /transform/upload` - Upload and transform image
- `GET /transformations` - Get transformation history
- `GET /transformations/{id}` - Get specific transformation
- `GET /download/{id}` - Download transformed image
- `DELETE /transformations/{id}` - Delete transformation

### Shopping Cart API (Port 8001)

- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /cart/add` - Add item to cart
- `GET /cart` - Get cart contents
- `PUT /cart/update/{product_id}` - Update cart item
- `DELETE /cart/remove/{product_id}` - Remove item from cart
- `DELETE /cart/clear` - Clear entire cart
- `GET /cart/count` - Get cart item count
- `POST /session/create` - Create user session
- `GET /session/{session_id}` - Get session data
- `DELETE /session/{session_id}` - Delete session
- `POST /cache/product/{product_id}` - Cache product data
- `GET /cache/product/{product_id}` - Get cached product
- `GET /redis/info` - Get Redis server info
- `POST /demo/setup` - Setup demo data

## 🚀 Usage Examples

### Stage 1: Basic Image Processing

```bash
# Run the basic image transformer
python3 main.py /path/to/image.jpg

# Use the enhanced transformer
python3 enhanced_image_transformer.py
```

### Stage 2: Web API Usage

```bash
# Start the API
python3 api.py

# Upload and transform an image
curl -X POST "http://localhost:8000/transform/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg" \
  -F "transformation_type=brightness" \
  -F "parameters={\"factor\": 1.3}"

# Get transformation history
curl "http://localhost:8000/transformations"
```

### Stage 3: Shopping Cart Usage

```bash
# Start the shopping cart API
python3 shopping_cart_api.py

# Add item to cart
curl -X POST "http://localhost:8001/cart/add" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "product_id": "laptop",
    "quantity": 1,
    "product_data": {
      "name": "MacBook Pro",
      "price": 1299.99
    }
  }'

# Get cart contents
curl "http://localhost:8001/cart" \
  -H "X-User-ID: user123"
```

### Stage 4: Redis Demo

```bash
# Run Redis functionality demo
python3 redis_demo.py
```

## 📊 Progression Summary

### ✅ **Completed Stages**

#### **Stage 1: Basic Python & OOP** ✅

- **`image_transformer.py`** - Core image processing class
  - NumPy array manipulation
  - OpenCV image transformations
  - Pillow image processing
  - Error handling and validation
- **`main.py`** - CLI interface (v1 - Basic)
  - Command-line argument processing
  - File system operations
  - User interaction
  - **No database storage**
- **`main_v2.py`** - Database integration (v2 - Stage 3+)
  - All v1 features plus database storage
  - Transformation history tracking
  - Progress monitoring
- **`main_v3.py`** - Advanced features (v3 - Stage 4+)
  - All v2 features plus advanced capabilities
  - Batch processing
  - Enhanced error handling
  - Configuration management
  - Performance monitoring
- **`calculator.py`** - Basic OOP example
  - Class definition and methods
  - Inheritance and polymorphism

#### **Stage 2: Advanced Image Processing** ✅

- **`enhanced_image_transformer.py`** - Extended functionality
  - Multiple transformation types
  - Performance optimization
  - Advanced image effects
- **`pillow_example.py`** - Pillow library demonstrations
  - Image filters and effects
  - Format conversion
  - Image manipulation
- **`image_reading_comparison.py`** - Library comparisons
  - OpenCV vs Pillow performance
  - Memory usage analysis
  - Best practices

#### **Stage 3: Web API Development** ✅

- **`api.py`** - FastAPI application
  - REST API endpoints
  - File upload handling
  - Database integration
  - Async programming
- **`config.py`** - Configuration management
  - Environment variables
  - Pydantic settings
  - Type safety
- **`database.py`** - PostgreSQL integration
  - SQLAlchemy ORM
  - Schema management
  - Connection pooling
- **`env_manager.py`** - Environment utilities
  - Variable validation
  - Type conversion
  - Security features

#### **Stage 4: Advanced Features** ✅

- **`redis_manager.py`** - Redis integration
  - Connection management
  - Shopping cart implementation
  - Session handling
  - Caching strategies
- **`shopping_cart_api.py`** - Microservice
  - Separate FastAPI service
  - Redis data structures
  - User sessions
  - Product caching
- **`redis_demo.py`** - Redis demonstrations
  - Data structure examples
  - Performance testing
  - Usage patterns

#### **Stage 5: Production Ready** ✅

- **`docker-compose.yml`** - Container orchestration
  - Multi-service setup
  - Environment configuration
  - Service dependencies
- **`start_db.sh`** / **`start_redis.sh`** - Service scripts
  - Automated startup
  - Health checks
  - Error handling
- **`init.sql`** - Database initialization
  - Schema creation
  - Index optimization
  - Data setup
- **`cleanup_public_schema.py`** - Maintenance
  - Safe cleanup procedures
  - Schema migration
  - Data preservation

### 📊 **Stage 6: Real-Time Features** ✅

- **`stage6_realtime_features.py`** - Real-time processing API
  - Server-Sent Events (SSE) for progress streaming
  - WebSocket connections for live updates
  - Redis pub/sub integration
  - Background processing with progress tracking
  - Real-time notifications
- **`stage6_client.html`** - Interactive web client
  - Real-time progress visualization
  - WebSocket connection management
  - Event logging and monitoring
  - Active transformation tracking

**Learning Focus:**

- Real-time communication patterns
- Event-driven architecture
- WebSocket and SSE implementation
- Background task processing
- Progress tracking and monitoring

### 🎯 **Key Learning Outcomes**

1. **Object-Oriented Programming**

   - Class design and inheritance
   - Method implementation
   - Encapsulation and abstraction

2. **Image Processing**

   - Multiple library integration
   - Performance optimization
   - Format handling

3. **Web Development**

   - FastAPI framework
   - REST API design
   - Async programming

4. **Database Integration**

   - PostgreSQL 16 features
   - SQLAlchemy ORM
   - Schema management

5. **Caching & Sessions**

   - Redis data structures
   - Shopping cart implementation
   - Session management

6. **Environment Management**

   - Configuration patterns
   - Security best practices
   - Type safety

7. **Containerization**
   - Docker setup
   - Service orchestration
   - Production deployment

### 🚀 **Next Steps**

1. **Authentication & Authorization**

   - JWT tokens
   - User management
   - Role-based access
   - OAuth2 integration
   - API key management

2. **File Upload & Processing**

   - **Large file uploads** - Chunked uploads, resume capability
   - **Batch processing** - Multiple file uploads and transformations
   - **File validation** - Type checking, virus scanning, size limits
   - **Storage optimization** - Compression, CDN integration
   - **Progress tracking** - Real-time upload progress
   - **Background processing** - Async file processing queues

3. **Server-Level Image Transformations**

   - **GPU acceleration** - CUDA/OpenCL integration
   - **Distributed processing** - Multi-server image processing
   - **Caching strategies** - Redis caching for transformed images
   - **Format conversion** - WebP, AVIF, HEIC support
   - **Thumbnail generation** - Automatic thumbnail creation
   - **Image optimization** - Quality/size optimization

4. **Real-Time Communication**

   - **Server-Sent Events (SSE)** - Real-time progress updates
   - **WebSockets** - Live transformation status
   - **Webhooks** - Event notifications to external services
   - **Pub/Sub** - Redis pub/sub for real-time messaging
   - **Event streaming** - Apache Kafka integration

5. **Event-Driven Architecture**

   - **Message queues** - RabbitMQ/Redis for async processing
   - **Event bus** - Centralized event management
   - **Event sourcing** - Event-driven data architecture
   - **CQRS** - Command Query Responsibility Segregation
   - **Saga patterns** - Distributed transaction management

6. **Machine Learning Integration**

   - **Image classification** - TensorFlow/PyTorch integration
   - **Object detection** - YOLO, Faster R-CNN
   - **Face recognition** - Face detection and recognition
   - **Image segmentation** - Semantic/instance segmentation
   - **Style transfer** - Neural style transfer
   - **Auto-enhancement** - AI-powered image enhancement
   - **Content moderation** - NSFW detection, content filtering

7. **Advanced Data Processing**

   - **Stream processing** - Apache Kafka Streams
   - **Data pipelines** - Apache Airflow integration
   - **ETL processes** - Data extraction, transformation, loading
   - **Real-time analytics** - Processing time, usage statistics
   - **A/B testing** - Image transformation experiments

8. **Microservices & Service Mesh**

   - **Service decomposition** - Break down into smaller services
   - **API Gateway** - Kong, Istio, or custom implementation
   - **Service discovery** - Consul, etcd, or Kubernetes
   - **Load balancing** - Round-robin, least connections
   - **Circuit breakers** - Resilience patterns
   - **Rate limiting** - API rate limiting and throttling

9. **Monitoring & Observability**

   - **Structured logging** - JSON logging with correlation IDs
   - **Metrics collection** - Prometheus, Grafana
   - **Distributed tracing** - Jaeger, Zipkin
   - **Health checks** - Liveness and readiness probes
   - **Performance monitoring** - APM tools (New Relic, DataDog)
   - **Error tracking** - Sentry integration

10. **Testing & Quality Assurance**

    - **Unit tests** - pytest with mocking
    - **Integration tests** - Database and API testing
    - **End-to-end tests** - Selenium, Playwright
    - **Performance testing** - Load testing with Locust
    - **Security testing** - OWASP ZAP, dependency scanning
    - **Code quality** - Black, flake8, mypy

11. **CI/CD & Deployment**

    - **GitHub Actions** - Automated testing and deployment
    - **Docker builds** - Multi-stage Docker builds
    - **Kubernetes** - Container orchestration
    - **Helm charts** - Kubernetes package management
    - **Blue-green deployment** - Zero-downtime deployments
    - **Rollback strategies** - Automated rollback mechanisms

12. **Advanced Features**

    - **Image metadata extraction** - EXIF data processing
    - **OCR integration** - Text extraction from images
    - **Barcode/QR code detection** - Automated scanning
    - **Image stitching** - Panorama creation
    - **Video processing** - Frame extraction, video transformations
    - **3D image processing** - Point cloud, mesh processing
    - **Geospatial processing** - GIS integration, map overlays

13. **Security & Compliance**

    - **Data encryption** - At-rest and in-transit encryption
    - **Access control** - RBAC, ABAC
    - **Audit logging** - Comprehensive audit trails
    - **GDPR compliance** - Data privacy and retention
    - **SOC 2 compliance** - Security controls
    - **Vulnerability scanning** - Regular security assessments

14. **Performance & Scalability**

    - **Horizontal scaling** - Auto-scaling based on load
    - **Database optimization** - Query optimization, indexing
    - **Caching layers** - Multi-level caching (Redis, CDN)
    - **Content delivery** - Global CDN distribution
    - **Database sharding** - Horizontal data partitioning
    - **Read replicas** - Database read scaling

15. **Developer Experience**

    - **API documentation** - OpenAPI/Swagger with examples
    - **SDK generation** - Client libraries for multiple languages
    - **CLI tools** - Command-line interface for operations
    - **Development environment** - Docker Compose for local development
    - **Code generation** - Scaffolding and boilerplate generation
    - **IDE integration** - VS Code extensions, IntelliJ plugins

16. **Business Intelligence**

    - **Usage analytics** - User behavior tracking
    - **Performance metrics** - System performance monitoring
    - **Cost optimization** - Resource usage tracking
    - **Business dashboards** - Real-time business metrics
    - **Predictive analytics** - Usage forecasting
    - **A/B testing framework** - Experimentation platform

17. **Integration & APIs**

    - **Third-party integrations** - AWS S3, Google Cloud Storage
    - **Webhook management** - Incoming/outgoing webhooks
    - **API versioning** - Semantic versioning strategy
    - **GraphQL** - Alternative to REST API
    - **gRPC** - High-performance RPC framework
    - **API marketplace** - Public API for third-party developers

18. **Disaster Recovery**

    - **Backup strategies** - Automated backup and recovery
    - **Multi-region deployment** - Geographic redundancy
    - **Failover mechanisms** - Automatic failover
    - **Data replication** - Cross-region data replication
    - **Recovery testing** - Regular disaster recovery drills
    - **Business continuity** - RTO/RPO planning

19. **Compliance & Governance**

    - **Data governance** - Data lineage, cataloging
    - **Compliance reporting** - Automated compliance reports
    - **Policy enforcement** - Automated policy checking
    - **Data retention** - Automated data lifecycle management
    - **Privacy controls** - Data anonymization, pseudonymization
    - **Regulatory compliance** - Industry-specific compliance

20. **Innovation & Research**

    - **AI/ML research** - Cutting-edge ML model integration
    - **Computer vision** - Advanced CV algorithms
    - **Edge computing** - Edge device processing
    - **Quantum computing** - Future quantum algorithms
    - **Blockchain integration** - Decentralized image processing
    - **AR/VR support** - Augmented/virtual reality processing

---

## 🎓 **Learning Path Summary**

This project demonstrates a **complete progression** from basic Python concepts to production-ready microservices:

- **Simple scripts** → **Complex applications**
- **Single files** → **Multi-service architecture**
- **Basic OOP** → **Advanced patterns**
- **Local processing** → **Distributed systems**
- **Manual setup** → **Automated deployment**

Each stage builds upon the previous one, ensuring a solid foundation for advanced concepts. The codebase serves as both a learning resource and a practical example of modern Python development practices.

**Happy Learning! 🎯**
