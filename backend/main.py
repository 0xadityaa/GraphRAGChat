import asyncio
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os

# Import the GraphRAG agent function
from graph_rag_agent import run_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GraphRAG Chatbot API",
    description="A FastAPI backend for GraphRAG chatbot using Google Cloud Spanner and Vertex AI",
    version="1.0.0"
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's question", min_length=1)
    conversation_id: str = Field(..., description="Unique conversation identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What products does Nestle offer?",
                "conversation_id": "conv_123456"
            }
        }

class Citation(BaseModel):
    url: str = Field(..., description="The source URL")
    title: Optional[str] = Field(None, description="Optional title of the source")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="The AI-generated response")
    citations: List[str] = Field(..., description="Array of citation URLs")
    conversation_id: str = Field(..., description="The conversation identifier")
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(..., description="Response timestamp")
    processing_time: float = Field(..., description="Time taken to process the request in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "Nestle offers a wide range of products including coffee, chocolate, pet food, and baby nutrition products.",
                "citations": [
                    "https://www.madewithnestle.ca/products",
                    "https://www.madewithnestle.ca/about"
                ],
                "conversation_id": "conv_123456",
                "message_id": "msg_789012",
                "timestamp": "2024-01-15T10:30:00Z",
                "processing_time": 2.34
            }
        }

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    conversation_id: str = Field(..., description="The conversation identifier")
    timestamp: datetime = Field(..., description="Error timestamp")

# In-memory storage for conversation history (in production, use a database)
conversation_history = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "GraphRAG Chatbot API is running",
        "status": "healthy",
        "timestamp": datetime.now()
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "service": "GraphRAG Chatbot API",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that processes user questions using GraphRAG
    
    Args:
        request: ChatRequest containing question and conversation_id
        
    Returns:
        ChatResponse with answer, citations, and metadata
    """
    start_time = asyncio.get_event_loop().time()
    message_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Processing chat request for conversation {request.conversation_id}")
        logger.info(f"Question: {request.question}")
        
        # Validate inputs
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if not request.conversation_id.strip():
            raise HTTPException(status_code=400, detail="Conversation ID cannot be empty")
        
        # Store conversation history (optional - for context in future messages)
        if request.conversation_id not in conversation_history:
            conversation_history[request.conversation_id] = []
        
        # Prepare conversation history for the agent (convert to the format expected by GraphRAG agent)
        formatted_history = []
        for msg in conversation_history[request.conversation_id]:
            # Add user message
            formatted_history.append({
                "role": "user",
                "content": msg["question"],
                "timestamp": msg["timestamp"].isoformat() if hasattr(msg["timestamp"], 'isoformat') else str(msg["timestamp"])
            })
            # Add assistant message
            formatted_history.append({
                "role": "assistant", 
                "content": msg["answer"],
                "timestamp": msg["timestamp"].isoformat() if hasattr(msg["timestamp"], 'isoformat') else str(msg["timestamp"])
            })
        
        # Run the GraphRAG agent with conversation history
        logger.info("Calling GraphRAG agent...")
        agent_result = await run_agent(request.question, formatted_history)
        
        # Extract answer and citations from agent result
        answer = agent_result.get("answer", "I couldn't generate an answer.")
        citations = agent_result.get("cited_sources", [])
        
        # Log the results
        logger.info(f"Agent response: {answer[:100]}...")
        logger.info(f"Citations found: {len(citations)}")
        
        # Store this interaction in conversation history
        conversation_history[request.conversation_id].append({
            "message_id": message_id,
            "question": request.question,
            "answer": answer,
            "citations": citations,
            "timestamp": datetime.now()
        })
        
        # Calculate processing time
        end_time = asyncio.get_event_loop().time()
        processing_time = round(end_time - start_time, 2)
        
        # Create response
        response = ChatResponse(
            answer=answer,
            citations=citations,
            conversation_id=request.conversation_id,
            message_id=message_id,
            timestamp=datetime.now(),
            processing_time=processing_time
        )
        
        logger.info(f"Successfully processed request in {processing_time}s")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        end_time = asyncio.get_event_loop().time()
        processing_time = round(end_time - start_time, 2)
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Internal server error: {str(e)}",
                "conversation_id": request.conversation_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time
            }
        )

@app.get("/conversations/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """
    Get conversation history for a specific conversation ID
    
    Args:
        conversation_id: The conversation identifier
        
    Returns:
        List of messages in the conversation
    """
    if conversation_id not in conversation_history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversation_history[conversation_id],
        "message_count": len(conversation_history[conversation_id])
    }

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and its history
    
    Args:
        conversation_id: The conversation identifier to delete
    """
    if conversation_id not in conversation_history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversation_history[conversation_id]
    return {
        "message": f"Conversation {conversation_id} deleted successfully",
        "timestamp": datetime.now()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 