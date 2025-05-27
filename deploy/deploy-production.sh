#!/bin/bash

# Production Deployment Script for GraphRAG to GCP Cloud Run

set -e

# Configuration
PROJECT_ID=${1:-""}
REGION=${2:-"us-central1"}
SERVICE_NAME="graphrag-backend"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    echo "Example: $0 my-gcp-project us-central1"
    exit 1
fi

echo "🚀 Deploying GraphRAG to GCP Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Set the project
gcloud config set project $PROJECT_ID

# Build and push the Docker image
echo "🐳 Building and pushing Docker image..."
IMAGE_URI="gcr.io/$PROJECT_ID/$SERVICE_NAME:$(date +%Y%m%d-%H%M%S)"
LATEST_URI="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

# Build the image
docker build -t $IMAGE_URI -t $LATEST_URI ./backend

# Push to Container Registry
docker push $IMAGE_URI
docker push $LATEST_URI

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URI \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 1 \
    --timeout 300 \
    --concurrency 10 \
    --service-account "graphrag-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
    --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,SPANNER_INSTANCE_ID=graphrag-instance,SPANNER_DATABASE_ID=graphrag-db,GOOGLE_CLOUD_LOCATION=$REGION" \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "🏥 Health Check: $SERVICE_URL/health"
echo "📚 API Docs: $SERVICE_URL/docs"
echo ""

# Test the deployment
echo "🧪 Testing deployment..."
if curl -f "$SERVICE_URL/health" >/dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    echo "Check the logs with: gcloud run logs read $SERVICE_NAME --region $REGION"
    exit 1
fi

echo ""
echo "🎉 GraphRAG backend is now live!"
echo ""
echo "Frontend Configuration:"
echo "Update your frontend to use this API endpoint:"
echo "REACT_APP_API_URL=$SERVICE_URL"
echo ""
echo "Example API call:"
echo "curl -X POST '$SERVICE_URL/chat' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"question\": \"What products does Nestle offer?\", \"conversation_id\": \"test-123\"}'" 