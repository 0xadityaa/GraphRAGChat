# GraphRAG Chatbot

A full-stack GraphRAG (Graph Retrieval-Augmented Generation) chatbot application built with FastAPI backend and Next.js frontend. The system leverages Google Cloud Spanner for graph storage, Vertex AI for embeddings and LLM capabilities, and deploys seamlessly to Google Cloud Platform.

## 🚀 Live Demo

- **Frontend**: https://frontend-471866182091.us-central1.run.app
- **Backend API**: https://graphrag-chatbot-471866182091.us-central1.run.app
- **API Documentation**: https://graphrag-chatbot-471866182091.us-central1.run.app/docs

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js       │────▶│   FastAPI       │────▶│   Google Cloud  │
│   Frontend      │     │   Backend       │     │   Spanner       │
│   (Port 3000)   │     │   (Port 8000)   │     │   (Graph DB)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │   Vertex AI     │
                        │   (LLM & Embed) │
                        └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Google Cloud Spanner**: Distributed SQL database for graph storage
- **Vertex AI**: LLM (text-bison) and embedding (textembedding-gecko) models
- **GraphRAG**: Knowledge graph-based retrieval augmented generation
- **Docker**: Containerization for consistent deployment

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
- **Google Cloud Build**: CI/CD pipeline
- **IAM & Security**: Service account-based authentication

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
- ✅ Dark/light theme support

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

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

### Metrics
- Response times via Cloud Run metrics
- Error rates via Cloud Logging
- Resource usage via Cloud Monitoring

## 🔒 Security

- Service account-based authentication
- IAM role-based access control
- Container security with non-root users
- Environment variable-based configuration
- CORS protection for frontend-backend communication

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**:
- Check Google Cloud credentials
- Verify Spanner instance and database exist
- Ensure all environment variables are set

**Frontend can't connect to backend**:
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS configuration in backend
- Ensure backend is accessible

**Deployment failures**:
- Check Docker image builds locally first
- Verify gcloud authentication and project
- Check Cloud Run service logs

### Debug Mode
Enable detailed logging:
```bash
# Backend
export LOG_LEVEL=DEBUG

# View detailed logs
docker-compose logs -f backend
```

## 📝 Development Notes

- The system automatically generates conversation IDs
- Citations are processed and displayed separately from responses
- All LLM responses are cleaned and formatted as markdown
- The backend supports streaming responses for real-time chat
- Frontend uses optimistic UI updates for better UX

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section above
- Review the API documentation at `/docs`
- Check Cloud Run logs for deployment issues
- Verify Google Cloud quotas and permissions

---

**Note**: Remember to update the URLs and project IDs in this README with your actual values before deploying. 