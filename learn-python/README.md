# Python Learning Path - Image Processing API

A comprehensive Python learning project that progresses from basic OOP to production-ready microservices with authentication, CI/CD, and real-time features.

## 🎯 Project Overview

This project demonstrates modern Python development practices through a progressive learning approach, building an image processing API with the following stages:

1. **Basic Python & OOP** - Core image transformation class
2. **Advanced Image Processing** - Multiple libraries and techniques
3. **Web API Development** - FastAPI with database integration
4. **Advanced Features** - Redis caching and sessions
5. **Production Ready** - Docker and environment management
6. **Real-Time Features** - SSE, WebSockets, and Pub/Sub
7. **Authentication & Security** - OAuth2 with JWT tokens
8. **CI/CD Pipeline** - Automated testing and deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (local or Docker)
- Redis (local or Docker)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd learn-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your database credentials

# Start services
docker-compose up -d postgres redis

# Run the application
python authenticated_file_upload_api.py
```

### Access the Application

- **Web Interface**: http://localhost:8004
- **API Documentation**: http://localhost:8004/docs
- **Health Check**: http://localhost:8004/health

## 📁 Project Structure

```
learn-python/
├── 📁 Core Files
│   ├── main.py                    # v1 - Basic image transformations
│   ├── main_v2.py                 # v2 - Database integration
│   ├── main_v3.py                 # v3 - Advanced features
│   ├── image_transformer.py       # Core image processing class
│   ├── authenticated_file_upload_api.py  # v4 - Authenticated API
│   └── auth_system.py             # OAuth2 authentication system
│
├── 📁 Database & Configuration
│   ├── database.py                # PostgreSQL database management
│   ├── config.py                  # Configuration management
│   ├── env.example                # Environment variables template
│   └── init.sql                   # Database initialization script
│
├── 📁 Advanced Features
│   ├── redis_manager.py           # Redis connection and management
│   ├── shopping_cart_api.py       # Redis shopping cart microservice
│   └── stage6_realtime_features.py # Real-time features (SSE, WebSockets)
│
├── 📁 Testing
│   ├── tests/                     # Test suite
│   │   ├── test_auth_system.py    # Authentication tests
│   │   └── test_image_transformer.py # Image processing tests
│   └── pytest.ini                 # Pytest configuration
│
├── 📁 CI/CD
│   ├── .github/workflows/         # GitHub Actions workflows
│   │   └── ci-cd.yml             # Main CI/CD pipeline
│   ├── Dockerfile                 # Multi-stage Docker build
│   └── docker-compose.yml         # Local development services
│
├── 📁 Documentation
│   ├── README.md                  # This file
│   ├── CI_CD_GUIDE.md            # CI/CD pipeline guide
│   ├── ENVIRONMENT_GUIDE.md       # Environment setup guide
│   ├── REDIS_GUIDE.md             # Redis usage guide
│   └── VERSION_COMPARISON.md      # Feature comparison
│
└── 📁 Data & Storage
    ├── uploads/                   # File uploads (user-specific)
    ├── output/                    # Transformed images
    └── logs/                      # Application logs
```

## 🔐 Authentication System

### Features

- **OAuth2 Authentication** with JWT tokens
- **Social Network Login** (Google, GitHub, Facebook - mock)
- **Role-Based Access Control** (Admin, User, Premium, Guest)
- **Secure Password Hashing** with bcrypt
- **Token Refresh** mechanism
- **User Management** and sessions

### Supported Authentication Methods

1. **Local Authentication**

   - Email/password login
   - Secure password hashing
   - Session management

2. **Social Network Authentication**

   - Google OAuth2 (mock)
   - GitHub OAuth2 (mock)
   - Facebook OAuth2 (mock)

3. **Mock Users for Testing**
   ```
   Admin:    admin@example.com / admin123
   User:     user@example.com / user123
   Premium:  premium@example.com / premium123
   ```

### API Endpoints

```bash
# Authentication
POST /token                    # Login with email/password
POST /oauth2/token            # Social login
GET  /users/me                # Get current user info

# File Operations (Authenticated)
POST /upload                  # Upload image file
POST /process/{upload_id}     # Process image
GET  /status/{upload_id}      # Get processing status
GET  /download/{upload_id}/{type} # Download result
GET  /preview/{upload_id}     # Image preview
GET  /uploads                 # List user uploads

# Admin Only
GET  /admin/users             # List all users
```

## 🏗️ CI/CD Pipeline

### Pipeline Stages

1. **Test & Lint** - Code quality and testing
2. **Security Scan** - Vulnerability scanning
3. **Build** - Docker image creation
4. **Deploy Staging** - Automatic staging deployment
5. **Deploy Production** - Manual production deployment
6. **Notify** - Status notifications

### Features

- **Automated Testing** with pytest and coverage
- **Code Quality** checks (flake8, black, isort, mypy)
- **Security Scanning** (bandit, safety)
- **Multi-platform Docker** builds
- **Environment-specific** deployments
- **Health checks** and monitoring

### Local Development

```bash
# Run tests
pytest tests/ -v --cov=. --cov-report=html

# Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
black --check --diff .
isort --check-only --diff .

# Run security scans
bandit -r . -f json -o bandit-report.json
safety check --json --output safety-report.json

# Build Docker image
docker build -t image-processing-api .
```

## 🎨 Image Processing Features

### Core Transformations

- **Color Adjustments**: Brightness, contrast, saturation, hue
- **Filters**: Sepia, grayscale, invert, Gaussian blur
- **Advanced**: Gamma correction, color temperature
- **Pillow Integration**: Additional transformation methods

### Supported Formats

- **Input**: JPG, JPEG, PNG, BMP, TIFF, WebP
- **Output**: JPG (configurable)

### Processing Options

- **Batch Processing** - Multiple transformations
- **Real-time Progress** - SSE and WebSocket updates
- **User-specific Storage** - Isolated file storage
- **Database History** - Transformation tracking

## 🗄️ Database Schema

### Tables

```sql
-- Users table (in-memory for demo)
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR NOT NULL,
    full_name VARCHAR,
    provider VARCHAR NOT NULL,
    provider_id VARCHAR,
    role VARCHAR DEFAULT 'user',
    status VARCHAR DEFAULT 'active',
    avatar_url VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Transformation history
CREATE TABLE transformation_history (
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

## 🔄 Real-Time Features

### Server-Sent Events (SSE)

- Real-time progress updates
- Processing status notifications
- Live transformation feedback

### WebSocket Support

- Bi-directional communication
- Live chat and notifications
- Real-time collaboration

### Redis Pub/Sub

- Event-driven architecture
- Message queuing
- Distributed processing

## 🐳 Docker Support

### Multi-stage Build

```dockerfile
# Builder stage
FROM python:3.11-slim as builder
# Install dependencies and build

# Runtime stage
FROM python:3.11-slim
# Copy built artifacts and run
```

### Features

- **Multi-platform** builds (linux/amd64, linux/arm64)
- **Security** - Non-root user
- **Health checks** - Automatic monitoring
- **Optimized** - Layer caching and minimal size

### Local Development

```bash
# Start services
docker-compose up -d

# Build and run application
docker build -t image-processing-api .
docker run -p 8004:8004 image-processing-api
```

## 📊 Monitoring and Observability

### Health Checks

- Database connectivity
- Redis connectivity
- File system access
- Application status

### Metrics

- Request count and duration
- Error rates
- Resource usage
- Custom business metrics

### Logging

- Structured JSON logging
- Correlation IDs
- Log levels (DEBUG, INFO, WARNING, ERROR)

## 🔒 Security Features

### Application Security

- **OAuth2** authentication
- **JWT tokens** with expiration
- **Password hashing** with bcrypt
- **Input validation** and sanitization
- **Rate limiting** and abuse prevention

### Infrastructure Security

- **Non-root containers**
- **Network policies**
- **Secrets management**
- **Access control**

### Code Security

- **Static analysis** with bandit
- **Dependency scanning** with safety
- **Code review** requirements
- **Vulnerability monitoring**

## 🧪 Testing Strategy

### Test Types

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Component interaction testing
3. **End-to-End Tests** - Full workflow testing
4. **Security Tests** - Vulnerability testing

### Test Coverage

- **Code Coverage** - 90%+ target
- **Security Coverage** - All critical paths
- **Performance Testing** - Load and stress testing

### Test Tools

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **pytest-asyncio** - Async testing
- **bandit** - Security testing

## 🚀 Deployment

### Environments

1. **Development** - Local development
2. **Staging** - Pre-production testing
3. **Production** - Live environment

### Deployment Strategies

- **Blue-Green** - Zero-downtime deployment
- **Rolling Updates** - Gradual deployment
- **Canary Releases** - Risk mitigation

### Infrastructure

- **Container Orchestration** - Kubernetes ready
- **Load Balancing** - High availability
- **Auto-scaling** - Performance optimization
- **Backup & Recovery** - Disaster recovery

## 📈 Performance Optimization

### Caching Strategy

- **Redis** - Session and data caching
- **CDN** - Static asset delivery
- **Database** - Query optimization

### Scaling

- **Horizontal** - Multiple instances
- **Vertical** - Resource optimization
- **Auto-scaling** - Dynamic scaling

### Monitoring

- **Application** - Performance metrics
- **Infrastructure** - Resource usage
- **Business** - User behavior

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch
3. **Develop** with tests
4. **Submit** a pull request
5. **Review** and merge

### Code Standards

- **PEP 8** - Python style guide
- **Type hints** - Type annotations
- **Documentation** - Docstrings and comments
- **Testing** - Comprehensive test coverage

### Quality Gates

- **Linting** - Code quality checks
- **Testing** - Automated testing
- **Security** - Vulnerability scanning
- **Performance** - Performance testing

## 📚 Learning Resources

### Python Concepts

- **OOP** - Classes, inheritance, polymorphism
- **Async Programming** - asyncio, async/await
- **Type Hints** - Static typing
- **Testing** - Unit and integration testing

### Web Development

- **FastAPI** - Modern web framework
- **REST APIs** - API design principles
- **Authentication** - OAuth2 and JWT
- **Real-time** - WebSockets and SSE

### DevOps

- **Docker** - Containerization
- **CI/CD** - Automated pipelines
- **Monitoring** - Observability
- **Security** - Best practices

## 🎯 Next Steps

### Planned Features

1. **Machine Learning Integration**

   - Image classification
   - Style transfer
   - Object detection

2. **Advanced Analytics**

   - Usage analytics
   - Performance metrics
   - User behavior tracking

3. **Microservices Architecture**

   - Service decomposition
   - API Gateway
   - Event-driven communication

4. **Cloud Deployment**
   - AWS/GCP/Azure support
   - Serverless deployment
   - Multi-region deployment

### Learning Path

1. **Basic Python** - Language fundamentals
2. **OOP Design** - Object-oriented programming
3. **Web Development** - FastAPI and REST APIs
4. **Database Integration** - PostgreSQL and SQLAlchemy
5. **Caching** - Redis and session management
6. **Authentication** - OAuth2 and security
7. **Real-time** - WebSockets and SSE
8. **DevOps** - Docker and CI/CD
9. **Production** - Monitoring and scaling

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **OpenCV** - Computer vision library
- **Pillow** - Image processing library
- **PostgreSQL** - Relational database
- **Redis** - In-memory data store
- **Docker** - Containerization platform
- **GitHub Actions** - CI/CD platform

---

**Happy Learning! 🚀**
