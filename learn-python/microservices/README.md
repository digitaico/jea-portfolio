# Microservices Architecture with Event-Driven Design

This project demonstrates a **modern microservices architecture** using **event-driven design** with **Redis Pub/Sub** for communication between services.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   Event Bus     │    │   Redis Pub/Sub │
│   (Port 8000)   │    │   (Port 8001)   │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Image Service   │    │  User Service   │    │  Auth Service   │
│ (Port 8002)     │    │  (Port 8003)    │    │  (Port 8004)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Notification Svc │    │   PostgreSQL    │    │  Redis Commander│
│(Port 8005)      │    │   (Port 5432)   │    │  (Port 8081)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Services

### 1. **API Gateway** (Port 8000)

- **Purpose**: Single entry point for all client requests
- **Features**:
  - Request routing and load balancing
  - Authentication and authorization
  - Rate limiting
  - Request/response transformation
  - CORS handling
  - Health checks for all services

### 2. **Event Bus** (Port 8001)

- **Purpose**: Central event management and routing
- **Features**:
  - Event publishing and subscription
  - Real-time event streaming via WebSockets
  - Event storage and retrieval
  - Event processing and routing
  - Event statistics and monitoring

### 3. **Image Processing Service** (Port 8002)

- **Purpose**: Handle image uploads, processing, and transformations
- **Features**:
  - Image upload and storage
  - Image processing and transformations
  - Background processing with progress tracking
  - File management and cleanup
  - Integration with existing image transformer

### 4. **User Service** (Port 8003)

- **Purpose**: User management and profiles
- **Features**:
  - User CRUD operations
  - User search and filtering
  - User statistics
  - Profile management
  - User roles and permissions

### 5. **Authentication Service** (Port 8004)

- **Purpose**: Authentication and authorization
- **Features**:
  - JWT token management
  - User registration and login
  - Password hashing and verification
  - Token refresh and validation
  - OAuth2 compatibility

### 6. **Notification Service** (Port 8005)

- **Purpose**: Notifications and messaging
- **Features**:
  - Real-time notifications via WebSockets
  - Email notifications (mock)
  - Notification management
  - Event-driven notifications
  - Notification statistics

## 🛠️ Technology Stack

### Core Technologies

- **Python 3.11** - Primary programming language
- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and settings management

### Communication

- **Redis Pub/Sub** - Event-driven communication
- **HTTP/REST** - Service-to-service communication
- **WebSockets** - Real-time communication

### Data Storage

- **PostgreSQL 16** - Primary database
- **Redis** - Caching and session storage

### Containerization

- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

### Monitoring & Management

- **Redis Commander** - Redis management UI (Port 8081)
- **pgAdmin** - PostgreSQL management UI (Port 8082)

## 🏃‍♂️ Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

### 1. Clone and Navigate

```bash
cd learn-python/microservices
```

### 2. Start All Services

```bash
docker-compose up -d
```

### 3. Check Service Status

```bash
# Check all services are running
docker-compose ps

# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

### 4. Access Management UIs

- **Redis Commander**: http://localhost:8081
- **pgAdmin**: http://localhost:8082 (admin@example.com / admin)

## 📊 API Endpoints

### API Gateway (Main Entry Point)

- **Base URL**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs

#### Authentication

```bash
# Register
POST /auth/register
{
  "email": "user@example.com",
  "username": "user",
  "password": "password123",
  "full_name": "Test User"
}

# Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Image Processing

```bash
# Upload image
POST /images/upload
# (multipart form with file and user_id)

# Process image
POST /images/{upload_id}/process
{
  "transformation_type": "grayscale",
  "parameters": {},
  "user_id": "user-001"
}

# Get processing status
GET /images/{upload_id}/status?user_id=user-001

# Download processed image
GET /images/{upload_id}/download/{transformation_type}?user_id=user-001
```

#### User Management

```bash
# Get current user
GET /users/me
# (requires Authorization header)

# Update user
PUT /users/me
{
  "full_name": "Updated Name"
}
```

#### Notifications

```bash
# Get notifications
GET /notifications?user_id=user-001

# Mark as read
PUT /notifications/{notification_id}/read?user_id=user-001
```

## 🔄 Event-Driven Communication

### Event Types

- `user.created` - User registration
- `user.updated` - User profile update
- `user.login` - User login
- `image.uploaded` - Image upload
- `image.processing.started` - Processing started
- `image.processing.completed` - Processing completed
- `image.processing.failed` - Processing failed
- `notification.sent` - Notification sent

### Event Flow Example

1. **User uploads image** → `image.uploaded` event
2. **Image service processes** → `image.processing.started` event
3. **Processing completes** → `image.processing.completed` event
4. **Notification service** → Creates notification
5. **Real-time notification** → Sent via WebSocket

## 🔧 Development

### Local Development

```bash
# Start only dependencies
docker-compose up -d redis postgres redis-commander pgadmin

# Run services locally
cd api-gateway && python -m uvicorn main:app --reload --port 8000
cd event-bus && python -m uvicorn main:app --reload --port 8001
cd image-service && python -m uvicorn main:app --reload --port 8002
cd user-service && python -m uvicorn main:app --reload --port 8003
cd auth-service && python -m uvicorn main:app --reload --port 8004
cd notification-service && python -m uvicorn main:app --reload --port 8005
```

### Testing

```bash
# Run tests for all services
pytest tests/ -v

# Run specific service tests
pytest tests/test_api_gateway.py -v
pytest tests/test_event_bus.py -v
```

### Logging

All services use structured logging with correlation IDs for request tracing.

## 📈 Monitoring and Health Checks

### Health Check Endpoints

- `GET /health` - Service health status
- `GET /services/health` - All services health (API Gateway)

### Metrics

- Request/response times
- Error rates
- Service uptime
- Event processing statistics

## 🔒 Security

### Authentication

- JWT tokens with expiration
- Refresh token mechanism
- Password hashing with bcrypt
- Role-based access control (RBAC)

### Authorization

- User roles: Admin, User, Premium, Guest
- Service-to-service authentication
- API rate limiting

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Configure all sensitive data
2. **Secrets Management**: Use proper secrets management
3. **SSL/TLS**: Enable HTTPS
4. **Load Balancing**: Use proper load balancers
5. **Monitoring**: Implement comprehensive monitoring
6. **Logging**: Centralized logging with ELK stack
7. **Database**: Use managed database services
8. **Caching**: Implement proper caching strategies

### Scaling

- **Horizontal Scaling**: Each service can be scaled independently
- **Load Balancing**: Use nginx or similar for API Gateway
- **Database**: Read replicas and connection pooling
- **Caching**: Redis clusters for high availability

## 📚 Learning Outcomes

This microservices architecture demonstrates:

1. **Event-Driven Architecture**: Using Redis Pub/Sub for loose coupling
2. **Service Decomposition**: Breaking down monolithic applications
3. **API Gateway Pattern**: Centralized entry point for all requests
4. **Real-time Communication**: WebSockets for live updates
5. **Containerization**: Docker for consistent deployments
6. **Service Discovery**: Internal service communication
7. **Health Monitoring**: Comprehensive health checks
8. **Security**: Authentication and authorization
9. **Scalability**: Independent service scaling
10. **Observability**: Logging, monitoring, and tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is for educational purposes and demonstrates modern microservices patterns.
