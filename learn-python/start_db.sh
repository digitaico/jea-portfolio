#!/bin/bash

# Start PostgreSQL 16 database using Docker Compose
# This script helps you get started with the database setup

set -e

echo "🚀 Starting PostgreSQL 16 database for Image Processor..."

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
        echo "📝 Please update .env with your database credentials"
    else
        echo "❌ env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
source .env

# Start the database
echo "🐘 Starting PostgreSQL 16 container..."
docker-compose up -d postgres

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Check if database is running
if docker-compose ps postgres | grep -q "Up"; then
    echo "✅ PostgreSQL 16 is running!"
    echo "📊 Database Details:"
    echo "  Host: ${DB_HOST:-localhost}"
    echo "  Port: ${DB_PORT:-5432}"
    echo "  Database: ${DB_NAME:-image_processor}"
    echo "  User: ${DB_USER:-postgres}"
    echo ""
    echo "🔗 Connection URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-password}@${DB_HOST:-localhost}:${DB_PORT:-5432}/${DB_NAME:-image_processor}"
    echo ""
    echo "🌐 Optional: pgAdmin is available at http://localhost:5050"
    echo "   Email: ${PGADMIN_EMAIL:-admin@example.com}"
    echo "   Password: ${PGADMIN_PASSWORD:-admin}"
    echo ""
    echo "📈 PostgreSQL 16 Features:"
    echo "  - Up to 25% faster query execution"
    echo "  - Enhanced parallel query processing"
    echo "  - Improved JSON/JSONB support"
    echo "  - Better monitoring and observability"
else
    echo "❌ Failed to start PostgreSQL 16. Check the logs:"
    docker-compose logs postgres
    exit 1
fi

echo ""
echo "🎯 Next steps:"
echo "1. Update your .env file with the correct database credentials"
echo "2. Run: python env_manager.py (to test environment variables)"
echo "3. Run: python api.py (to start the FastAPI server)"
echo "4. Visit: http://localhost:8000/docs (for API documentation)"
echo "5. Visit: http://localhost:5050 (for pgAdmin)" 