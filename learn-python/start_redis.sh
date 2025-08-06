#!/bin/bash

# Start Redis and related services using Docker Compose
# This script helps you get started with Redis setup

set -e

echo "🚀 Starting Redis services for Shopping Cart..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env from env.example"
        echo "📝 Please update .env with your Redis credentials if needed"
    else
        echo "❌ env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
source .env

# Start Redis services
echo "🔴 Starting Redis container..."
docker-compose up -d redis

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
sleep 3

# Check if Redis is running
if docker-compose ps redis | grep -q "Up"; then
    echo "✅ Redis is running!"
    echo "📊 Redis Details:"
    echo "  Host: ${REDIS_HOST:-localhost}"
    echo "  Port: ${REDIS_PORT:-6379}"
    echo "  Database: ${REDIS_DB:-0}"
    echo ""
    echo "🔗 Connection URL: redis://${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}/${REDIS_DB:-0}"
    echo ""
    echo "🌐 Optional: Redis Commander is available at http://localhost:8081"
    echo "   Username: ${REDIS_COMMANDER_USER:-admin}"
    echo "   Password: ${REDIS_COMMANDER_PASSWORD:-admin}"
else
    echo "❌ Failed to start Redis. Check the logs:"
    docker-compose logs redis
    exit 1
fi

# Start Redis Commander if not already running
echo "🔍 Starting Redis Commander..."
docker-compose up -d redis-commander

# Wait for Redis Commander to be ready
sleep 2

if docker-compose ps redis-commander | grep -q "Up"; then
    echo "✅ Redis Commander is running at http://localhost:8081"
else
    echo "⚠️  Redis Commander failed to start. Check logs:"
    docker-compose logs redis-commander
fi

echo ""
echo "🎯 Next steps:"
echo "1. Test Redis connection: python3 redis_demo.py"
echo "2. Start shopping cart API: python3 shopping_cart_api.py"
echo "3. Visit API docs: http://localhost:8001/docs"
echo "4. Visit Redis Commander: http://localhost:8081"
echo ""
echo "🔧 Useful commands:"
echo "  View Redis logs: docker-compose logs -f redis"
echo "  Stop services: docker-compose down"
echo "  Restart Redis: docker-compose restart redis" 