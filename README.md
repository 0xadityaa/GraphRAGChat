# GraphRAG Chatbot

A full-stack GraphRAG (Graph Retrieval Augmented Generation) chatbot application built with FastAPI + Langchain backend and Next.js frontend. The system leverages Google Cloud Spanner for graph storage, Vertex AI for embeddings (text-embedding-004) and LLM (Gemini 2.5 flash) capabilities, and deploys seamlessly to Google Cloud Platform.

## Live Demo

- **Frontend**: https://frontend-471866182091.us-central1.run.app
- **Backend API**: https://graphrag-chatbot-471866182091.us-central1.run.app
- **API Documentation**: https://graphrag-chatbot-471866182091.us-central1.run.app/docs

## Architecture
![Mermaid Chart Editor May 29 2025 (2)](https://github.com/user-attachments/assets/13baae3f-ae51-43d8-9587-1faf8d0d1ea4)


#### GraphRAG Workflow
![Mermaid Chart Editor May 29 2025 (1)](https://github.com/user-attachments/assets/0a561d2f-9757-4c49-82d8-6e53c12fadbe)


#### Data Scraping and Ingestion workflow
![Mermaid Chart Editor May 29 2025](https://github.com/user-attachments/assets/cc25a1bd-d7ab-45a7-826d-cccf3967f198)


## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Google Cloud Spanner**: Distributed SQL database for graph storage
- **Vertex AI**: LLM (text-bison) and embedding (textembedding-gecko) models
- **GraphRAG**: Knowledge graph-based retrieval augmented generation
- **Docker**: Containerization for consistent deployment
- **Crawl4AI*: Playwright based web scrapper for collecting site data

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Headless UI components
- **React Hook Form**: Form management
- **Markdown Rendering**: Rich response formatting

### Infrastructure
- **Google Cloud Run**: Serverless container deployment
- **Google Container Registry**: Docker image storage
- **Google Spanner DB**: Managed Graph DB for knowledge graph
- **Google Vertex AI**: LLM and Embeddings modals

## 📋 Prerequisites

Before starting, ensure you have:

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed locally
4. **Node.js 18+** and **Python 3.11+**
5. **Service Account Key** with appropriate permissions

### Required Google Cloud APIs
- Cloud Spanner API
- Vertex AI API
- Cloud Run API
- Cloud Build API
- Container Registry API

## 🚀 Quick Start

### Option 1: Local Development with Docker

```bash
# Clone the repository
git clone <your-repo-url>
cd GraphRAG-Chatbot

# Start all services with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Local Setup

```bash
# 1. Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start backend
python start_server.py

# 2. Frontend Setup (in new terminal)
cd frontend
npm install  # or pnpm install
npm run dev
```

## 🔧 Detailed Setup

### 1. Environment Configuration

Create the following environment files:

**Backend (`backend/.env`)**:
```env
GCP_PROJECT_ID=your-project-id
SPANNER_INSTANCE_ID=graphrag-instance
SPANNER_DATABASE_ID=graphrag-db
GOOGLE_APPLICATION_CREDENTIALS_PATH=../GraphRAG-IAM-Admin.json
GOOGLE_CLOUD_LOCATION=us-central1
```

**Frontend (`frontend/.env.local`)**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Google Cloud Setup

#### Create Service Account
```bash
# Create service account
gcloud iam service-accounts create graphrag-service-account \
    --display-name="GraphRAG Service Account"

# Create and download key
gcloud iam service-accounts keys create GraphRAG-IAM-Admin.json \
    --iam-account=graphrag-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:graphrag-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:graphrag-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

#### Create Spanner Instance and Database
```bash
# Create Spanner instance
gcloud spanner instances create graphrag-instance \
    --config=regional-us-central1 \
    --description="GraphRAG Instance" \
    --nodes=1

# Create database
gcloud spanner databases create graphrag-db \
    --instance=graphrag-instance
```

### 3. Data Ingestion

Before using the chatbot, populate your knowledge graph:

```bash
cd backend
python ingest_data.py
```

Or use the scraper to collect web data:
```bash
cd scraper
python scraper.py
```

## 🐳 Docker Configuration

### Local Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Build Individual Images
```bash
# Backend
cd backend
docker build -t graphrag-backend .

# Frontend
cd frontend
docker build -t graphrag-frontend .
```

## ☁️ Google Cloud Deployment

### Deploy Backend to Cloud Run

```bash
cd backend

# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/graphrag-backend .

# Deploy to Cloud Run
gcloud run deploy graphrag-backend \
    --image gcr.io/YOUR_PROJECT_ID/graphrag-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --concurrency 10 \
    --timeout 300 \
    --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID,SPANNER_INSTANCE_ID=graphrag-instance,SPANNER_DATABASE_ID=graphrag-db,GOOGLE_CLOUD_LOCATION=us-central1
```

### Deploy Frontend to Cloud Run

```bash
cd frontend

# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/graphrag-frontend .

# Deploy to Cloud Run
gcloud run deploy graphrag-frontend \
    --image gcr.io/YOUR_PROJECT_ID/graphrag-frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 3000 \
    --set-env-vars NEXT_PUBLIC_API_URL=https://YOUR_BACKEND_URL
```

## 🔌 API Documentation

### Core Endpoints

#### POST `/chat`
Send a message to the chatbot:
```json
{
  "question": "What products does Nestle offer?",
  "conversation_id": "conv_123456"
}
```

Response:
```json
{
  "answer": "Nestle offers a wide range of products including...",
  "citations": ["https://www.madewithnestle.ca/products"],
  "conversation_id": "conv_123456",
  "message_id": "msg_789012",
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time": 2.34
}
```

#### GET `/conversations/{conversation_id}`
Retrieve conversation history

#### DELETE `/conversations/{conversation_id}`
Clear conversation history

#### GET `/health`
Backend health check

### Interactive API Documentation
Visit `/docs` endpoint for Swagger UI documentation when running the backend.

## 🎯 Features

### Backend Features
- ✅ GraphRAG-based question answering
- ✅ Conversation history management
- ✅ Source citation tracking
- ✅ Google Cloud Spanner integration
- ✅ Vertex AI LLM and embeddings
- ✅ FastAPI with automatic documentation
- ✅ Docker containerization
- ✅ Health check endpoints

### Frontend Features
- ✅ Modern chat interface
- ✅ Real-time messaging
- ✅ Markdown response rendering
- ✅ Source citation display
- ✅ Conversation management
- ✅ Loading states and error handling
- ✅ Responsive design

### Health Checks
```bash
# Local
curl http://localhost:8000/health

# Production
curl https://your-backend-url/health
```

## 📊 Monitoring

### Logs
```bash
# Local Docker logs
docker-compose logs -f backend

# Cloud Run logs
gcloud run logs read graphrag-backend --region us-central1
```
