# Redis Shopping Cart Guide

A comprehensive guide to using Redis for shopping cart functionality, session management, and caching in Python applications.

## 🎯 Why Redis for Shopping Cart?

Redis is perfect for shopping carts because:

- **Speed**: In-memory operations are extremely fast
- **Data Structures**: Native support for hashes, lists, sets
- **Expiration**: Automatic cleanup of old data
- **Persistence**: Optional data persistence
- **Scalability**: Horizontal scaling capabilities
- **Real-time**: Perfect for real-time applications

## 🚀 Quick Start

### 1. Start Redis

```bash
# Using Docker Compose
./start_redis.sh

# Or manually
docker-compose up -d redis redis-commander
```

### 2. Test Connection

```bash
# Run the demo
python3 redis_demo.py

# Or test manually
python3 -c "from redis_manager import cart_manager; print('Connected:', cart_manager.is_connected())"
```

### 3. Start Shopping Cart API

```bash
# Start the API
python3 shopping_cart_api.py

# Visit docs
# http://localhost:8001/docs
```

## 📁 Redis Data Structures

### 1. Shopping Cart (Hash)

```redis
# Key format: cart:{user_id}
cart:user123 -> {
  "prod_001": '{"quantity": 2, "price": 99.99, "name": "Laptop"}',
  "prod_002": '{"quantity": 1, "price": 29.99, "name": "Mouse"}'
}
```

### 2. Sessions (String with Expiry)

```redis
# Key format: session:{session_id}
session:user123_1234567890 -> '{"user_id": "user123", "cart_count": 3, "last_activity": 1234567890}'
```

### 3. Product Cache (String with Expiry)

```redis
# Key format: product:{product_id}
product:laptop_001 -> '{"name": "MacBook Pro", "price": 1299.99, "description": "High-performance laptop"}'
```

## 🔧 Core Operations

### Shopping Cart Operations

```python
from redis_manager import cart_manager

# Add item to cart
cart_manager.add_to_cart(
    user_id="user123",
    product_id="laptop",
    quantity=2,
    product_data={
        "name": "MacBook Pro",
        "price": 1299.99,
        "description": "High-performance laptop"
    }
)

# Get cart contents
cart = cart_manager.get_cart("user123")
print(f"Cart has {len(cart)} items")

# Update quantity
cart_manager.update_cart_item("user123", "laptop", 3)

# Remove item
cart_manager.remove_from_cart("user123", "laptop")

# Clear cart
cart_manager.clear_cart("user123")

# Get cart count
count = cart_manager.get_cart_count("user123")
```

### Session Management

```python
# Create session
session_data = {
    "user_id": "user123",
    "cart_count": 3,
    "last_activity": time.time(),
    "preferences": {"theme": "dark", "language": "en"}
}
session_id = cart_manager.create_session("user123", session_data)

# Get session
session = cart_manager.get_session(session_id)

# Delete session
cart_manager.delete_session(session_id)
```

### Product Caching

```python
# Cache product
product_data = {
    "name": "Gaming Headset",
    "price": 89.99,
    "description": "7.1 surround sound gaming headset"
}
cart_manager.cache_product("headset_001", product_data)

# Get cached product
product = cart_manager.get_cached_product("headset_001")
```

## 🌐 API Endpoints

### Shopping Cart API

| Method   | Endpoint                    | Description           |
| -------- | --------------------------- | --------------------- |
| `POST`   | `/cart/add`                 | Add item to cart      |
| `GET`    | `/cart`                     | Get cart contents     |
| `PUT`    | `/cart/update/{product_id}` | Update cart item      |
| `DELETE` | `/cart/remove/{product_id}` | Remove item from cart |
| `DELETE` | `/cart/clear`               | Clear entire cart     |
| `GET`    | `/cart/count`               | Get cart item count   |

### Session Management

| Method   | Endpoint                | Description         |
| -------- | ----------------------- | ------------------- |
| `POST`   | `/session/create`       | Create user session |
| `GET`    | `/session/{session_id}` | Get session data    |
| `DELETE` | `/session/{session_id}` | Delete session      |

### Caching

| Method | Endpoint                      | Description        |
| ------ | ----------------------------- | ------------------ |
| `POST` | `/cache/product/{product_id}` | Cache product data |
| `GET`  | `/cache/product/{product_id}` | Get cached product |

### Monitoring

| Method | Endpoint      | Description                    |
| ------ | ------------- | ------------------------------ |
| `GET`  | `/health`     | Health check with Redis status |
| `GET`  | `/redis/info` | Redis server information       |

## 📊 Example Usage

### Using the API

```bash
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

# Get cart
curl "http://localhost:8001/cart" \
  -H "X-User-ID: user123"

# Update quantity
curl -X PUT "http://localhost:8001/cart/update/laptop?quantity=2" \
  -H "X-User-ID: user123"

# Remove item
curl -X DELETE "http://localhost:8001/cart/remove/laptop" \
  -H "X-User-ID: user123"
```

### Using Python Client

```python
import requests

# Add to cart
response = requests.post(
    "http://localhost:8001/cart/add",
    headers={"X-User-ID": "user123"},
    json={
        "product_id": "laptop",
        "quantity": 1,
        "product_data": {
            "name": "MacBook Pro",
            "price": 1299.99
        }
    }
)

# Get cart
response = requests.get(
    "http://localhost:8001/cart",
    headers={"X-User-ID": "user123"}
)
cart = response.json()
print(f"Cart total: ${cart['total_price']}")
```

## 🔍 Redis Commands

### Manual Redis Operations

```bash
# Connect to Redis CLI
docker exec -it image_processor_redis redis-cli

# View all cart keys
KEYS cart:*

# Get cart contents
HGETALL cart:user123

# Get specific item
HGET cart:user123 laptop

# Set expiry on cart
EXPIRE cart:user123 86400

# View all sessions
KEYS session:*

# Get Redis info
INFO
```

### Redis Commander

Access Redis Commander at http://localhost:8081:

- **Username**: `admin`
- **Password**: `admin`

Features:

- Browse Redis keys
- View and edit data
- Monitor Redis performance
- Execute Redis commands

## 🏗️ Architecture

### Data Flow

```
User Request → FastAPI → Redis Manager → Redis
                ↓
            Response ← JSON ← Parsed Data ← Redis
```

### Key Design Patterns

1. **Repository Pattern**: `RedisManager` abstracts Redis operations
2. **Factory Pattern**: Connection pooling and configuration
3. **Strategy Pattern**: Different data structures for different use cases
4. **Observer Pattern**: Automatic expiry and cleanup

### Performance Considerations

- **Connection Pooling**: Reuse connections for better performance
- **Pipelining**: Batch operations when possible
- **Expiration**: Automatic cleanup prevents memory bloat
- **Serialization**: JSON for complex data, simple types for basic data

## 🔒 Security Best Practices

### 1. Authentication

```python
# In production, use JWT tokens
def get_user_id(authorization: str = Header(...)) -> str:
    # Validate JWT token
    token = authorization.replace("Bearer ", "")
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload["user_id"]
```

### 2. Data Validation

```python
# Validate input data
from pydantic import BaseModel, Field

class CartItem(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., ge=1, le=1000)
    product_data: Optional[ProductData] = None
```

### 3. Rate Limiting

```python
# Implement rate limiting
from fastapi import HTTPException
import time

def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    current = cart_manager.redis.incr(key)
    if current == 1:
        cart_manager.redis.expire(key, 60)  # 1 minute window

    if current > 100:  # Max 100 requests per minute
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from redis_manager import ShoppingCartManager

@pytest.fixture
def cart_manager():
    return ShoppingCartManager()

def test_add_to_cart(cart_manager):
    success = cart_manager.add_to_cart("test_user", "test_product", 1)
    assert success == True

    cart = cart_manager.get_cart("test_user")
    assert "test_product" in cart
```

### Integration Tests

```python
from fastapi.testclient import TestClient
from shopping_cart_api import app

client = TestClient(app)

def test_add_to_cart_api():
    response = client.post(
        "/cart/add",
        headers={"X-User-ID": "test_user"},
        json={
            "product_id": "laptop",
            "quantity": 1,
            "product_data": {"name": "Laptop", "price": 999.99}
        }
    )
    assert response.status_code == 200
```

## 📈 Monitoring

### Health Checks

```python
@app.get("/health")
async def health_check():
    redis_info = cart_manager.get_redis_info()
    return {
        "status": "healthy" if cart_manager.is_connected() else "unhealthy",
        "redis": redis_info,
        "timestamp": time.time()
    }
```

### Metrics

```python
# Track cart operations
def track_cart_operation(operation: str, user_id: str):
    key = f"metrics:cart:{operation}:{user_id}"
    cart_manager.redis.incr(key)
    cart_manager.redis.expire(key, 86400)  # 24 hours
```

## 🚀 Production Deployment

### Docker Compose

```yaml
version: "3.8"
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped

  app:
    build: .
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - redis
```

### Environment Variables

```bash
# Production .env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-password
REDIS_DB=0
REDIS_URL=redis://:your-secure-password@redis:6379/0
```

## 🎯 Key Takeaways

1. **Redis is Fast**: In-memory operations provide excellent performance
2. **Data Structures Matter**: Choose the right structure for your use case
3. **Expiration is Key**: Automatic cleanup prevents memory issues
4. **Connection Management**: Use connection pooling for better performance
5. **Error Handling**: Always handle Redis connection failures gracefully
6. **Monitoring**: Track Redis performance and usage
7. **Security**: Implement proper authentication and validation

## 📚 Next Steps

1. **Add Authentication**: JWT tokens, user management
2. **Implement Caching**: Cache frequently accessed data
3. **Add Analytics**: Track user behavior and cart patterns
4. **Scale Horizontally**: Redis Cluster for high availability
5. **Add Persistence**: RDB and AOF for data durability
6. **Implement Queues**: Use Redis for job queues and background tasks

---

**Happy Redis Learning! 🔴**
