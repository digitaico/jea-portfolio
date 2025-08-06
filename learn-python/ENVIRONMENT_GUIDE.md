# Environment Variable Management Guide

A comprehensive guide to managing environment variables in Python applications using `python-dotenv`.

## 🎯 Why Environment Variables?

Environment variables are essential for:

- **Security**: Keep sensitive data (passwords, API keys) out of code
- **Configuration**: Different settings for different environments
- **Flexibility**: Easy to change settings without code changes
- **Best Practices**: Industry standard for configuration management

## 🚀 Quick Start

### 1. Install python-dotenv

```bash
pip install python-dotenv
```

### 2. Create .env file

```bash
# Copy template
cp env.example .env

# Edit with your values
nano .env
```

### 3. Load in your code

```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Use environment variables
database_url = os.getenv('DATABASE_URL', 'default_url')
debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
```

## 📁 File Structure

```
learn-python/
├── .env                    # Environment variables (create from template)
├── env.example            # Template file
├── config.py              # Pydantic settings configuration
├── env_manager.py         # Custom environment manager
├── env_example.py         # Comprehensive examples
└── ENVIRONMENT_GUIDE.md   # This guide
```

## 🔧 Basic Usage

### Loading Environment Variables

```python
from dotenv import load_dotenv
import os

# Load .env file (searches current directory and parents)
load_dotenv()

# Get environment variables with defaults
app_name = os.getenv('APP_NAME', 'Default App')
debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
port = int(os.getenv('PORT', '8000'))
```

### Type Conversion

```python
# Integer conversion
max_file_size = int(os.getenv('MAX_FILE_SIZE', '10485760'))

# Boolean conversion
debug_enabled = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')

# Float conversion
timeout = float(os.getenv('TIMEOUT', '30.0'))

# List conversion (comma-separated)
allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# JSON conversion
import json
config = json.loads(os.getenv('CONFIG_JSON', '{}'))
```

## 🏗️ Advanced Usage with Pydantic

### Using Pydantic Settings

```python
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Default App"
    debug: bool = False
    port: int = 8000
    database_url: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create settings instance
settings = Settings()
print(f"App: {settings.app_name}, Debug: {settings.debug}, Port: {settings.port}")
```

### Environment Variable Mapping

```python
class Settings(BaseSettings):
    database_url: str = "postgresql://localhost:5432/default"

    class Config:
        env_file = ".env"
        fields = {
            'database_url': {'env': 'DATABASE_URL'},
        }
```

## 🛠️ Custom Environment Manager

### EnvManager Class

```python
from env_manager import EnvManager

# Initialize manager
env = EnvManager()

# Get typed values
port = env.get_int('API_PORT', 8000)
debug = env.get_bool('DEBUG', True)
max_size = env.get_int('MAX_FILE_SIZE', 10485760)

# Validate required variables
required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
if env.validate_required(required_vars):
    print("✅ All required variables are set")

# Print summary
env.print_summary(include_values=False)
```

### Key Features

1. **Type Safety**: Automatic type conversion
2. **Validation**: Required variable checking
3. **Security**: Masks sensitive values
4. **Flexibility**: Supports various data types
5. **Error Handling**: Graceful fallbacks

## 📝 .env File Structure

### Basic Template

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=database
DB_USER=username
DB_PASSWORD=password

# Application Configuration
APP_NAME=My Application
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
MAX_FILE_SIZE=10485760

# Optional: External Services
REDIS_URL=redis://localhost:6379
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
```

### Environment-Specific Files

```bash
# .env.local (local development)
DEBUG=True
LOG_LEVEL=DEBUG

# .env.production (production)
DEBUG=False
LOG_LEVEL=WARNING
```

## 🔒 Security Best Practices

### 1. Never Commit .env Files

```bash
# .gitignore
.env
.env.local
.env.production
.env.*.local
```

### 2. Use Strong Defaults

```python
# Good: Strong default
secret_key = os.getenv('SECRET_KEY', 'change-me-in-production')

# Bad: Weak default
secret_key = os.getenv('SECRET_KEY', '123456')
```

### 3. Validate Required Variables

```python
def validate_environment():
    required_vars = ['DATABASE_URL', 'SECRET_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
```

### 4. Mask Sensitive Values

```python
def print_config_safe():
    config = {
        'app_name': os.getenv('APP_NAME'),
        'debug': os.getenv('DEBUG'),
        'database_url': '***' if os.getenv('DATABASE_URL') else None,
        'secret_key': '***' if os.getenv('SECRET_KEY') else None,
    }
    print(config)
```

## 🐳 Docker Integration

### Docker Compose with Environment

```yaml
version: "3.8"
services:
  app:
    image: myapp:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DEBUG=${DEBUG}
    env_file:
      - .env
```

### Environment File in Docker

```dockerfile
# Dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install python-dotenv

CMD ["python", "app.py"]
```

## 🧪 Testing Environment Variables

### Test Script

```python
# test_env.py
import os
from dotenv import load_dotenv

def test_environment():
    load_dotenv()

    # Test required variables
    required = ['DATABASE_URL', 'SECRET_KEY']
    for var in required:
        value = os.getenv(var)
        if not value:
            print(f"❌ Missing: {var}")
        else:
            print(f"✅ Found: {var}")

    # Test optional variables
    optional = ['DEBUG', 'PORT', 'LOG_LEVEL']
    for var in optional:
        value = os.getenv(var, 'default')
        print(f"📝 {var}: {value}")

if __name__ == "__main__":
    test_environment()
```

## 🔍 Debugging Environment Variables

### Common Issues

1. **File not found**: Ensure `.env` file exists in correct directory
2. **Wrong format**: Use `KEY=value` format (no spaces around `=`)
3. **Case sensitivity**: Environment variables are case-sensitive
4. **Quotes**: Don't quote values unless needed for spaces

### Debug Commands

```bash
# Check if .env file exists
ls -la .env

# View .env contents (be careful with sensitive data)
cat .env

# Test environment loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DEBUG'))"

# Run environment test
python env_example.py
```

## 📚 Integration Examples

### FastAPI Application

```python
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    debug: bool = False
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

@app.get("/")
async def root():
    return {"message": f"Hello from {settings.app_name}"}
```

### Database Connection

```python
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_database_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    return psycopg2.connect(database_url)
```

## 🎯 Best Practices Summary

1. **Always use defaults**: Provide sensible defaults for optional variables
2. **Validate early**: Check required variables at startup
3. **Type conversion**: Convert strings to appropriate types
4. **Security first**: Never commit sensitive data
5. **Environment-specific**: Use different .env files for different environments
6. **Documentation**: Document all environment variables
7. **Testing**: Test environment configuration in CI/CD

## 🚀 Next Steps

1. **Update your .env file** with actual database credentials
2. **Test the configuration** with `python env_example.py`
3. **Start the database** with `./start_db.sh`
4. **Run the API** with `python api.py`
5. **Explore the documentation** at http://localhost:8000/docs

---

**Happy Environment Management! 🌍**
