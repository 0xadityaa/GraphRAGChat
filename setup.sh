#!/bin/bash

# GraphRAG Chatbot Setup Script
# This script helps set up the project for local development

set -e

echo "🚀 GraphRAG Chatbot Setup Script"
echo "=================================="

# Check if required tools are installed
check_dependencies() {
    echo "📋 Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! command -v gcloud &> /dev/null; then
        echo "⚠️  gcloud CLI is not installed. This is required for GCP deployment."
        echo "   You can still run locally, but won't be able to deploy to GCP."
    fi
    
    echo "✅ Dependencies check complete!"
}

# Create environment file if it doesn't exist
setup_env() {
    echo "🔧 Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "⚠️  Please edit .env with your actual values before running the application"
    else
        echo "✅ .env file already exists"
    fi
}

# Check for service account key
check_service_account() {
    echo "🔑 Checking for service account key..."
    
    if [ ! -f GraphRAG-IAM-Admin.json ]; then
        echo "⚠️  GraphRAG-IAM-Admin.json not found"
        echo "   Please place your Google Cloud service account key file in the root directory"
        echo "   This file is required for authentication with Google Cloud services"
    else
        echo "✅ Service account key found"
    fi
}

# Pull Docker images (optional, for faster startup)
pull_images() {
    echo "🐳 Pulling base Docker images (this may take a while)..."
    
    docker pull node:18-alpine
    docker pull python:3.11-slim
    
    echo "✅ Base images pulled successfully"
}

# Build and start services
start_services() {
    echo "🚀 Building and starting services..."
    
    # Build images
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "📊 To view logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 To stop services:"
    echo "   docker-compose down"
}

# Main setup flow
main() {
    echo "Starting GraphRAG Chatbot setup..."
    echo ""
    
    check_dependencies
    echo ""
    
    setup_env
    echo ""
    
    check_service_account
    echo ""
    
    # Ask user if they want to pull images
    read -p "📥 Do you want to pull base Docker images now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pull_images
        echo ""
    fi
    
    # Ask user if they want to start services
    read -p "🚀 Do you want to build and start the services now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
    else
        echo "⏸️  Skipping service startup"
        echo "   To start services later, run: docker-compose up -d"
    fi
    
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Edit .env with your Google Cloud configuration"
    echo "   2. Place GraphRAG-IAM-Admin.json in the root directory"
    echo "   3. Run 'docker-compose up -d' to start the services"
    echo "   4. Visit http://localhost:3000 to use the application"
    echo ""
    echo "📚 For more information, see the README.md file"
}

# Run main function
main "$@" 