#!/bin/bash

# GraphRAG Chatbot GCP Deployment Script
# This script automates the deployment to Google Cloud Platform

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"graphrag-460523"}
REGION=${REGION:-"us-central1"}
BACKEND_SERVICE_NAME="graphrag-backend"
FRONTEND_SERVICE_NAME="graphrag-frontend"

echo "🚀 GraphRAG Chatbot GCP Deployment Script"
echo "=========================================="
echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Backend Service: $BACKEND_SERVICE_NAME"
echo "   Frontend Service: $FRONTEND_SERVICE_NAME"
echo ""

# Check if gcloud is installed and authenticated
check_gcloud() {
    echo "🔍 Checking gcloud configuration..."
    
    if ! command -v gcloud &> /dev/null; then
        echo "❌ gcloud CLI is not installed. Please install it first:"
        echo "   https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo "❌ gcloud is not authenticated. Please run:"
        echo "   gcloud auth login"
        exit 1
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    echo "✅ gcloud configuration verified"
}

# Enable required APIs
enable_apis() {
    echo "🔧 Enabling required Google Cloud APIs..."
    
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        containerregistry.googleapis.com \
        --project=$PROJECT_ID
    
    echo "✅ APIs enabled successfully"
}

# Deploy backend to Cloud Run
deploy_backend() {
    echo "🚀 Deploying backend to Cloud Run..."
    
    cd backend
    
    # Build and push Docker image
    echo "🐳 Building and pushing backend Docker image..."
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME .
    
    # Deploy to Cloud Run
    echo "☁️  Deploying backend to Cloud Run..."
    gcloud run deploy $BACKEND_SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 1 \
        --concurrency 10 \
        --timeout 300 \
        --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,SPANNER_INSTANCE_ID=graphrag-instance,SPANNER_DATABASE_ID=graphrag-db,GOOGLE_CLOUD_LOCATION=$REGION
    
    # Get backend URL
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
    echo "✅ Backend deployed successfully at: $BACKEND_URL"
    
    cd ..
}

# Deploy frontend to Cloud Run
deploy_frontend() {
    echo "🚀 Deploying frontend to Cloud Run..."
    
    if [ -z "$BACKEND_URL" ]; then
        echo "❌ Backend URL not found. Please deploy backend first."
        exit 1
    fi
    
    cd frontend
    
    # Build and push Docker image with backend URL
    echo "🐳 Building and pushing frontend Docker image..."
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME \
        --substitutions=_NEXT_PUBLIC_API_URL=$BACKEND_URL .
    
    # Deploy to Cloud Run
    echo "☁️  Deploying frontend to Cloud Run..."
    gcloud run deploy $FRONTEND_SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 3000 \
        --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL
    
    # Get frontend URL
    FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
    echo "✅ Frontend deployed successfully at: $FRONTEND_URL"
    
    cd ..
}

# Test deployments
test_deployments() {
    echo "🧪 Testing deployments..."
    
    # Test backend health
    echo "🔍 Testing backend health endpoint..."
    if curl -s "$BACKEND_URL/health" | grep -q "healthy"; then
        echo "✅ Backend health check passed"
    else
        echo "⚠️  Backend health check failed"
    fi
    
    # Test frontend
    echo "🔍 Testing frontend..."
    if curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200"; then
        echo "✅ Frontend is accessible"
    else
        echo "⚠️  Frontend accessibility test failed"
    fi
}

# Display final information
show_summary() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================="
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: $FRONTEND_URL"
    echo "   Backend:  $BACKEND_URL"
    echo "   API Docs: $BACKEND_URL/docs"
    echo ""
    echo "📊 Monitoring:"
    echo "   Backend Logs: gcloud run logs read $BACKEND_SERVICE_NAME --region $REGION"
    echo "   Frontend Logs: gcloud run logs read $FRONTEND_SERVICE_NAME --region $REGION"
    echo ""
    echo "🔧 Management:"
    echo "   Update Backend: cd backend && gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME ."
    echo "   Update Frontend: cd frontend && gcloud builds submit --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME ."
    echo ""
    echo "💡 Tips:"
    echo "   - Monitor costs in the Google Cloud Console"
    echo "   - Set up alerts for unusual traffic patterns"
    echo "   - Consider setting up CI/CD for automatic deployments"
}

# Main deployment flow
main() {
    echo "Starting deployment to Google Cloud Platform..."
    echo ""
    
    # Check for project ID override
    if [ "$1" != "" ]; then
        PROJECT_ID=$1
        echo "📝 Using project ID from argument: $PROJECT_ID"
    fi
    
    # Check for region override
    if [ "$2" != "" ]; then
        REGION=$2
        echo "📝 Using region from argument: $REGION"
    fi
    
    check_gcloud
    echo ""
    
    enable_apis
    echo ""
    
    deploy_backend
    echo ""
    
    deploy_frontend
    echo ""
    
    test_deployments
    echo ""
    
    show_summary
}

# Show usage if help is requested
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [PROJECT_ID] [REGION]"
    echo ""
    echo "Arguments:"
    echo "  PROJECT_ID  Google Cloud Project ID (default: $PROJECT_ID)"
    echo "  REGION      Google Cloud Region (default: $REGION)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Use default project and region"
    echo "  $0 my-project               # Use custom project, default region"
    echo "  $0 my-project us-west1      # Use custom project and region"
    echo ""
    echo "Environment Variables:"
    echo "  GCP_PROJECT_ID  Override default project ID"
    echo "  REGION          Override default region"
    exit 0
fi

# Run main function
main "$@" 