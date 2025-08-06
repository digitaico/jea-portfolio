# CI/CD Pipeline Guide

## Overview

This project implements a comprehensive CI/CD (Continuous Integration/Continuous Deployment) pipeline using GitHub Actions. The pipeline automates testing, building, security scanning, and deployment processes.

## Pipeline Architecture

```mermaid
graph TD
    A[Code Push/PR] --> B[Test & Lint]
    B --> C[Security Scan]
    C --> D[Build Docker Image]
    D --> E{Environment}
    E -->|develop| F[Deploy to Staging]
    E -->|release| G[Deploy to Production]
    F --> H[Smoke Tests]
    G --> I[Health Checks]
    H --> J[Notify]
    I --> J
    J --> K[Pipeline Complete]
```

## Pipeline Stages

### 1. Test and Lint (`test` job)

**Purpose**: Ensure code quality and functionality

**Services**:

- PostgreSQL 16 (test database)
- Redis 7.4 (test cache)

**Steps**:

1. **Checkout**: Clone repository
2. **Setup Python**: Install Python 3.11
3. **Cache Dependencies**: Cache pip packages
4. **Install Dependencies**: Install requirements and test tools
5. **Linting**: Run flake8, black, isort
6. **Type Checking**: Run mypy
7. **Testing**: Run pytest with coverage
8. **Upload Coverage**: Send coverage to Codecov

**Tools Used**:

- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `flake8`: Code linting
- `black`: Code formatting
- `isort`: Import sorting
- `mypy`: Type checking

### 2. Security Scan (`security` job)

**Purpose**: Identify security vulnerabilities

**Steps**:

1. **Bandit Scan**: Python security linter
2. **Safety Check**: Dependency vulnerability scan
3. **Upload Reports**: Store security reports as artifacts

**Tools Used**:

- `bandit`: Security linting
- `safety`: Dependency vulnerability scanning

### 3. Build Docker Image (`build` job)

**Purpose**: Create production-ready Docker image

**Triggers**: Push to main/develop or release

**Steps**:

1. **Setup Buildx**: Multi-platform Docker builds
2. **Login to Registry**: Authenticate with GitHub Container Registry
3. **Extract Metadata**: Generate image tags and labels
4. **Build and Push**: Build multi-platform image and push to registry

**Features**:

- Multi-platform builds (linux/amd64, linux/arm64)
- Layer caching for faster builds
- Automatic tagging based on git events

### 4. Deploy to Staging (`deploy-staging` job)

**Purpose**: Deploy to staging environment for testing

**Triggers**: Push to `develop` branch

**Steps**:

1. **Deploy**: Apply staging configuration
2. **Smoke Tests**: Verify deployment health

### 5. Deploy to Production (`deploy-production` job)

**Purpose**: Deploy to production environment

**Triggers**: Release published

**Steps**:

1. **Deploy**: Apply production configuration
2. **Health Checks**: Verify production health

### 6. Notify (`notify` job)

**Purpose**: Send notifications about deployment status

**Triggers**: Always (success or failure)

## Configuration Files

### GitHub Actions Workflow

**File**: `.github/workflows/ci-cd.yml`

**Key Features**:

- Multi-job pipeline with dependencies
- Environment-specific deployments
- Comprehensive testing and security scanning
- Docker image building and publishing
- Automated notifications

### Docker Configuration

**File**: `Dockerfile`

**Features**:

- Multi-stage build for optimization
- Non-root user for security
- Health checks
- Minimal runtime image

**Stages**:

1. **Builder**: Install dependencies and build
2. **Runtime**: Copy built artifacts and run

## Environment Variables

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=image_processor
DB_USER=postgres
DB_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Application
SECRET_KEY=your-secret-key-here
DEBUG=false
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8004
API_PREFIX=/api/v1

# File Storage
UPLOAD_DIR=uploads
OUTPUT_DIR=output
MAX_FILE_SIZE=10485760
```

### GitHub Secrets

Configure these secrets in your GitHub repository:

```bash
# Database
DATABASE_URL
DB_PASSWORD

# Redis
REDIS_PASSWORD

# Application
SECRET_KEY

# Docker Registry (auto-configured)
GITHUB_TOKEN
```

## Local Development

### Running Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov flake8 black isort mypy

# Run tests
pytest tests/ -v --cov=. --cov-report=html

# Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
black --check --diff .
isort --check-only --diff .

# Run type checking
mypy . --ignore-missing-imports
```

### Running Security Scans Locally

```bash
# Install security tools
pip install bandit safety

# Run security scans
bandit -r . -f json -o bandit-report.json
safety check --json --output safety-report.json
```

### Building Docker Image Locally

```bash
# Build image
docker build -t image-processing-api .

# Run container
docker run -p 8004:8004 \
  -e DATABASE_URL=postgresql://user:pass@host:port/db \
  -e REDIS_URL=redis://localhost:6379/0 \
  -e SECRET_KEY=your-secret-key \
  image-processing-api
```

## Deployment Strategies

### Staging Deployment

**Purpose**: Test changes before production

**Strategy**:

- Automatic deployment on `develop` branch
- Smoke tests to verify functionality
- Rollback capability

**Environment**:

- Separate database and Redis instances
- Load balancer for high availability
- Monitoring and logging

### Production Deployment

**Purpose**: Serve live traffic

**Strategy**:

- Manual deployment via GitHub releases
- Blue-green deployment for zero downtime
- Health checks and monitoring

**Environment**:

- Production-grade infrastructure
- Auto-scaling capabilities
- Backup and disaster recovery

## Monitoring and Observability

### Health Checks

**Endpoint**: `GET /health`

**Checks**:

- Database connectivity
- Redis connectivity
- Application status
- File system access

### Metrics

**Prometheus Metrics**:

- Request count and duration
- Error rates
- Resource usage
- Custom business metrics

### Logging

**Structured Logging**:

- JSON format for easy parsing
- Correlation IDs for request tracking
- Log levels (DEBUG, INFO, WARNING, ERROR)

## Security Considerations

### Code Security

- **Bandit**: Static analysis for security issues
- **Safety**: Dependency vulnerability scanning
- **Code review**: Required for all changes
- **Secrets management**: Secure storage of sensitive data

### Infrastructure Security

- **Non-root containers**: Run as non-privileged user
- **Network policies**: Restrict network access
- **Secrets rotation**: Regular secret updates
- **Access control**: Role-based access

### Application Security

- **OAuth2**: Secure authentication
- **JWT tokens**: Stateless session management
- **Input validation**: Sanitize all inputs
- **Rate limiting**: Prevent abuse

## Troubleshooting

### Common Issues

1. **Test Failures**

   - Check database connectivity
   - Verify Redis connection
   - Review test logs

2. **Build Failures**

   - Check Dockerfile syntax
   - Verify dependencies
   - Review build logs

3. **Deployment Failures**
   - Check environment variables
   - Verify infrastructure access
   - Review deployment logs

### Debug Commands

```bash
# Check container logs
docker logs <container-id>

# Check application status
curl -f http://localhost:8004/health

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check Redis connectivity
redis-cli -u $REDIS_URL ping
```

## Best Practices

### Code Quality

- Write comprehensive tests
- Follow PEP 8 style guide
- Use type hints
- Document code and APIs

### Security

- Never commit secrets
- Use least privilege principle
- Regular security updates
- Monitor for vulnerabilities

### Performance

- Optimize Docker images
- Use caching effectively
- Monitor resource usage
- Scale appropriately

### Reliability

- Implement health checks
- Use circuit breakers
- Monitor and alert
- Plan for failures

## Future Enhancements

### Planned Features

1. **Advanced Testing**

   - Integration tests
   - Performance tests
   - Chaos engineering

2. **Enhanced Security**

   - SAST/DAST scanning
   - Container scanning
   - Compliance checks

3. **Improved Monitoring**

   - Distributed tracing
   - Custom dashboards
   - Alert automation

4. **Deployment Options**
   - Kubernetes deployment
   - Serverless deployment
   - Multi-region deployment

### Automation Opportunities

1. **Auto-scaling**

   - Based on metrics
   - Predictive scaling
   - Cost optimization

2. **Self-healing**

   - Automatic restarts
   - Health-based routing
   - Failure recovery

3. **GitOps**
   - Infrastructure as code
   - Automated rollbacks
   - Configuration management
