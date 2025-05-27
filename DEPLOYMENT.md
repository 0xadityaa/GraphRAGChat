# GraphRAG Chatbot Deployment Guide

This guide covers how to dockerize and deploy your GraphRAG chatbot to Google Cloud Platform (GCP) using Cloud Run.

## 🏗️ Architecture Overview

- **Backend**: FastAPI application with GraphRAG functionality
- **Database**: Google Cloud Spanner for graph storage
- **AI**: Vertex AI for embeddings and LLM
- **Deployment**: Cloud Run for serverless container hosting
- **CI/CD**: Cloud Build for automated deployments

## 📋 Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed locally
4. **Service Account Key** (`GraphRAG-IAM-Admin.json`) in project root
5. **Spanner Instance** and database already created

## 🚀 Quick Start

### 1. Local Development

```bash
# Clone and navigate to project
cd GraphRAG-Chatbot

# Set up local environment
./deploy/local-dev.sh

# Your API will be available at http://localhost:8000
```

### 2. Production Deployment

```bash
# Set up GCP resources (one-time)
./deploy/setup-gcp.sh YOUR_PROJECT_ID us-central1

# Deploy to production
./deploy/deploy-production.sh YOUR_PROJECT_ID us-central1
```

## 📝 Detailed Setup

### Step 1: Environment Configuration

Create a `.env` file in the project root:

```env
# GCP Configuration
GCP_PROJECT_ID=your-project-id
SPANNER_INSTANCE_ID=graphrag-instance
SPANNER_DATABASE_ID=graphrag-db
GOOGLE_APPLICATION_CREDENTIALS_PATH=./GraphRAG-IAM-Admin.json
GOOGLE_CLOUD_LOCATION=us-central1
```

### Step 2: GCP Resources Setup

The setup script will:
- Enable required APIs
- Create service accounts
- Set IAM permissions
- Create secrets for credentials

```bash
./deploy/setup-gcp.sh YOUR_PROJECT_ID
```

### Step 3: Data Ingestion

Before deploying, ensure your knowledge graph is populated:

```bash
# Run locally first
cd backend
python ingest_data.py

# Or run via Docker
docker-compose --profile scraper up scraper
```

### Step 4: Deploy to Cloud Run

```bash
./deploy/deploy-production.sh YOUR_PROJECT_ID
```

## 🐳 Docker Configuration

### Backend Dockerfile Features

- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Health checks** for reliability
- **Environment variable** configuration
- **Production-ready** uvicorn setup

### Local Development with Docker Compose

```bash
# Start backend only
docker-compose up backend

# Run scraper (one-time)
docker-compose --profile scraper up scraper

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## ☁️ Cloud Run Configuration

### Resource Allocation

- **Memory**: 2GB
- **CPU**: 1 vCPU
- **Concurrency**: 10 requests per instance
- **Timeout**: 300 seconds
- **Auto-scaling**: 1-10 instances

### Environment Variables

The deployment automatically sets:
- `GCP_PROJECT_ID`
- `SPANNER_INSTANCE_ID`
- `SPANNER_DATABASE_ID`
- `GOOGLE_CLOUD_LOCATION`

### Service Account Permissions

The service account has these roles:
- `roles/spanner.databaseUser`
- `roles/aiplatform.user`
- `roles/secretmanager.secretAccessor`
- `roles/logging.logWriter`

## 🔧 CI/CD with Cloud Build

### Automatic Deployment

The `cloudbuild.yaml` configuration provides:
- **Automated builds** on code changes
- **Container registry** push
- **Cloud Run deployment**
- **Health check validation**

### Manual Trigger

```bash
gcloud builds submit --config=cloudbuild.yaml . \
  --substitutions=_SPANNER_INSTANCE_ID=graphrag-instance,_SPANNER_DATABASE_ID=graphrag-db
```

## 🌐 Frontend Integration

Update your frontend to use the deployed API:

```javascript
// React example
const API_BASE_URL = 'https://graphrag-backend-[hash]-uc.a.run.app';

const response = await fetch(`${API_BASE_URL}/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'What products does Nestle offer?',
    conversation_id: 'user-123'
  })
});

const data = await response.json();
console.log(data.answer); // Markdown formatted response
```

## 📊 Monitoring and Logging

### Health Checks

- **Endpoint**: `/health`
- **Local**: http://localhost:8000/health
- **Production**: https://your-service-url/health

### Viewing Logs

```bash
# Cloud Run logs
gcloud run logs read graphrag-backend --region us-central1

# Cloud Build logs
gcloud builds log [BUILD_ID]

# Local logs
docker-compose logs -f backend
```

### API Documentation

- **Local**: http://localhost:8000/docs
- **Production**: https://your-service-url/docs

## 🔒 Security Considerations

1. **Service Account**: Uses least-privilege principle
2. **Secrets Management**: Credentials stored in Secret Manager
3. **Non-root Container**: Runs as unprivileged user
4. **HTTPS Only**: Cloud Run enforces HTTPS
5. **CORS Configuration**: Properly configured for frontend

## 🐛 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs
   gcloud builds log [BUILD_ID]
   ```

2. **Service Not Starting**
   ```bash
   # Check service logs
   gcloud run logs read graphrag-backend --region us-central1
   ```

3. **Permission Errors**
   ```bash
   # Verify service account permissions
   gcloud projects get-iam-policy YOUR_PROJECT_ID
   ```

4. **Local Development Issues**
   ```bash
   # Check container logs
   docker-compose logs backend
   
   # Rebuild containers
   docker-compose build --no-cache
   ```

### Health Check Failures

If health checks fail:
1. Verify environment variables are set correctly
2. Check Spanner instance is accessible
3. Ensure service account has proper permissions
4. Review application logs for errors

## 📈 Scaling and Performance

### Auto-scaling Configuration

Cloud Run automatically scales based on:
- **Request volume**
- **CPU utilization**
- **Memory usage**

### Performance Optimization

1. **Cold Start Reduction**: Minimum 1 instance
2. **Concurrency**: Optimized for 10 requests/instance
3. **Resource Allocation**: 2GB memory for LLM operations
4. **Caching**: Implement Redis for conversation history (optional)

## 💰 Cost Optimization

1. **Pay-per-use**: Only charged when serving requests
2. **Auto-scaling**: Scales to zero when idle
3. **Resource Efficiency**: Optimized container size
4. **Regional Deployment**: Choose closest region to users

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Deploy new version
./deploy/deploy-production.sh YOUR_PROJECT_ID

# Rollback if needed
gcloud run services replace-traffic graphrag-backend --to-revisions=PREVIOUS_REVISION=100
```

### Database Migrations

```bash
# Run data ingestion for updates
python backend/ingest_data.py
```

## 📞 Support

For issues:
1. Check the logs first
2. Verify GCP quotas and limits
3. Review IAM permissions
4. Test locally with Docker Compose

---

**Your GraphRAG chatbot is now ready for production! 🎉**

The deployed API will return responses in markdown format, perfect for your frontend to render rich content with proper formatting. 