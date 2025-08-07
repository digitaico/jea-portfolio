#!/bin/bash

# Microservices Startup Script
# This script starts the complete microservices architecture

set -e

echo "🚀 Starting Microservices Architecture..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ docker compose is not available. Please install it first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p output

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
services=(
    "http://localhost:8000/health"
    "http://localhost:8001/health"
    "http://localhost:8002/health"
    "http://localhost:8003/health"
    "http://localhost:8004/health"
    "http://localhost:8005/health"
)

for service in "${services[@]}"; do
    echo "Checking $service..."
    if curl -f -s "$service" > /dev/null; then
        echo "✅ Service is healthy: $service"
    else
        echo "❌ Service is not responding: $service"
    fi
done

echo ""
echo "🎉 Microservices Architecture is running!"
echo ""
echo "📊 Service URLs:"
echo "  • API Gateway:        http://localhost:8000"
echo "  • API Documentation:  http://localhost:8000/docs"
echo "  • Event Bus:          http://localhost:8001"
echo "  • Image Service:      http://localhost:8002"
echo "  • User Service:       http://localhost:8003"
echo "  • Auth Service:       http://localhost:8004"
echo "  • Notification Svc:   http://localhost:8005"
echo ""
echo "🛠️  Management UIs:"
echo "  • Redis Commander:    http://localhost:8081"
echo "  • pgAdmin:           http://localhost:8082 (admin@example.com / admin)"
echo ""
echo "🔍 Useful Commands:"
echo "  • View logs:         docker-compose logs -f"
echo "  • Stop services:     docker-compose down"
echo "  • Restart services:  docker-compose restart"
echo "  • Check status:      docker-compose ps"
echo ""
echo "📝 Sample API Calls:"
echo "  • Health check:      curl http://localhost:8000/health"
echo "  • Register user:     curl -X POST http://localhost:8000/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"password123\"}'"
echo ""
echo "🎯 Next Steps:"
echo "  1. Open http://localhost:8000/docs to explore the API"
echo "  2. Try registering a user and uploading an image"
echo "  3. Check the event bus at http://localhost:8001 for real-time events"
echo "  4. Monitor Redis at http://localhost:8081"
echo ""
