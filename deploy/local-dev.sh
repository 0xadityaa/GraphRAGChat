#!/bin/bash

# Local Development Setup Script for GraphRAG

set -e

echo "🏠 Setting up local development environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << EOF
# GCP Configuration
GCP_PROJECT_ID=your-project-id
SPANNER_INSTANCE_ID=graphrag-instance
SPANNER_DATABASE_ID=graphrag-db
GOOGLE_APPLICATION_CREDENTIALS_PATH=./GraphRAG-IAM-Admin.json
GOOGLE_CLOUD_LOCATION=us-central1

# Local Development
HOST=0.0.0.0
PORT=8000
RELOAD=true
LOG_LEVEL=info
EOF
    echo "⚠️  Please update the .env file with your actual GCP project details"
fi

# Check if credentials file exists
if [ ! -f "GraphRAG-IAM-Admin.json" ]; then
    echo "❌ GraphRAG-IAM-Admin.json not found!"
    echo "Please download your service account key and place it in the project root"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data/content

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting backend service..."
docker-compose up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
timeout=60
counter=0
while ! curl -f http://localhost:8000/health >/dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Backend failed to start within $timeout seconds"
        docker-compose logs backend
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done

echo ""
echo "✅ Backend is ready!"
echo ""
echo "🌐 Services available at:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "📊 To view logs:"
echo "  docker-compose logs -f backend"
echo ""
echo "🛑 To stop services:"
echo "  docker-compose down"
echo ""
echo "🔄 To run scraper (one-time):"
echo "  docker-compose --profile scraper up scraper" 