# GraphRAG Chatbot Integration Setup

This document explains how to set up and run the integrated GraphRAG chatbot with FastAPI backend and Next.js frontend.

## Architecture Overview

- **Backend**: FastAPI server with GraphRAG agent using Google Cloud Spanner and Vertex AI
- **Frontend**: Next.js React application with modern chat UI components
- **Integration**: REST API communication with real-time chat functionality

## Prerequisites

1. **Backend Requirements**:
   - Python 3.11+
   - Google Cloud Project with Spanner and Vertex AI enabled
   - Service account credentials (GraphRAG-IAM-Admin.json)
   - Required Python packages (see backend/requirements.txt)

2. **Frontend Requirements**:
   - Node.js 18+
   - npm/pnpm/yarn package manager

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Google Cloud settings:
# GCP_PROJECT_ID=your-project-id
# SPANNER_INSTANCE_ID=your-instance-id
# SPANNER_DATABASE_ID=your-database-id
# GOOGLE_APPLICATION_CREDENTIALS_PATH=../GraphRAG-IAM-Admin.json

# Start the FastAPI server
python start_server.py
# Or directly: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or: pnpm install

# Configure API URL (optional)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the development server
npm run dev
# or: pnpm dev
```

The frontend will be available at `http://localhost:3000`

### 3. Testing the Integration

1. **Health Check**: Visit `http://localhost:8000/health` to verify backend is running
2. **API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs
3. **Chat Interface**: Visit `http://localhost:3000` and use the chat widget in the bottom-right corner

## Features

### Chat Functionality
- ✅ Real-time messaging with FastAPI backend
- ✅ Conversation management with unique IDs
- ✅ Loading states and error handling
- ✅ Markdown rendering for rich responses
- ✅ Citation links with source URLs
- ✅ Conversation clearing and reset

### UI Components
- ✅ Expandable chat widget
- ✅ Message bubbles with avatars
- ✅ Source citation display
- ✅ Auto-scrolling message list
- ✅ Input validation and disabled states
- ✅ Error message display

### Backend Integration
- ✅ GraphRAG agent with Spanner and Vertex AI
- ✅ Conversation history tracking
- ✅ Citation URL processing and formatting
- ✅ Response cleaning and markdown formatting
- ✅ Error handling and logging

## API Endpoints

### POST /chat
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
  "answer": "Nestle offers a wide range of products...",
  "citations": ["https://www.madewithnestle.ca/products"],
  "conversation_id": "conv_123456",
  "message_id": "msg_789012",
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time": 2.34
}
```

### GET /conversations/{conversation_id}
Get conversation history

### DELETE /conversations/{conversation_id}
Clear conversation history

### GET /health
Backend health check

## Configuration

### Environment Variables

**Backend (.env)**:
```env
GCP_PROJECT_ID=your-project-id
SPANNER_INSTANCE_ID=your-instance-id
SPANNER_DATABASE_ID=your-database-id
GOOGLE_APPLICATION_CREDENTIALS_PATH=../GraphRAG-IAM-Admin.json
GOOGLE_CLOUD_LOCATION=us-central1
```

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the backend CORS middleware allows your frontend origin
2. **API Connection Failed**: Check that backend is running on port 8000
3. **Google Cloud Errors**: Verify credentials file path and permissions
4. **Citation Links Not Working**: Check URL formatting in the backend response

### Debug Mode

Enable debug logging in the backend:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check browser console for frontend errors and network requests.

## Development Notes

- The chat component automatically generates conversation IDs
- Citations are processed to remove URL encoding and format properly
- LLM responses are cleaned to remove citation sections (handled separately)
- Error states are displayed in the chat interface
- The backend supports conversation history for context-aware responses

## Production Deployment

For production deployment:

1. **Backend**: Deploy to Google Cloud Run or similar container service
2. **Frontend**: Deploy to Vercel, Netlify, or similar static hosting
3. **Environment**: Update `NEXT_PUBLIC_API_URL` to production backend URL
4. **Security**: Configure proper CORS origins and authentication if needed 