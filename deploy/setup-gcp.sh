#!/bin/bash

# GraphRAG GCP Setup Script
# This script sets up the necessary GCP resources for deploying the GraphRAG chatbot

set -e

# Configuration
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
SERVICE_ACCOUNT_NAME="graphrag-service-account"
CREDENTIALS_FILE="GraphRAG-IAM-Admin.json"

echo "🚀 Setting up GCP resources for GraphRAG deployment..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    spanner.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com

# Create service account if it doesn't exist
echo "👤 Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com >/dev/null 2>&1; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="GraphRAG Service Account" \
        --description="Service account for GraphRAG chatbot"
fi

# Grant necessary IAM roles
echo "🔐 Granting IAM roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# Create secret for service account credentials
echo "🔑 Creating secret for credentials..."
if [ -f "../$CREDENTIALS_FILE" ]; then
    gcloud secrets create graphrag-credentials \
        --data-file="../$CREDENTIALS_FILE" \
        --replication-policy="automatic" || echo "Secret already exists"
    
    # Grant access to the secret
    gcloud secrets add-iam-policy-binding graphrag-credentials \
        --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
else
    echo "⚠️  Warning: $CREDENTIALS_FILE not found. Please create the secret manually."
fi

# Set up Cloud Build trigger (optional)
echo "🔨 Setting up Cloud Build..."
gcloud builds submit --config=../cloudbuild.yaml .. \
    --substitutions=_SPANNER_INSTANCE_ID=graphrag-instance,_SPANNER_DATABASE_ID=graphrag-db

echo "✅ GCP setup complete!"
echo ""
echo "Next steps:"
echo "1. Ensure your Spanner instance and database are created"
echo "2. Run the data ingestion script to populate the knowledge graph"
echo "3. Test the deployment with: curl https://graphrag-backend-[hash]-uc.a.run.app/health"
echo ""
echo "Your backend will be available at:"
echo "https://graphrag-backend-[hash]-uc.a.run.app" 