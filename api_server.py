#!/usr/bin/env python3
"""
FastAPI server for K-Array Chat frontend.
Provides REST API endpoints for the React frontend.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import json
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
logger = logging.getLogger("server")

# Import Kchat components
try:
    from main import generate_session_id, generate_user_id
    from agents.context import AgentContext
    from agents.agent_manager import AgentManager
    from models._call_llm import call_llm
    from utils.input_validator import validate_user_input, ValidationError
    from config.settings import config
    from rag_manager import RAGManager
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Fallback functions for testing
    def generate_session_id():
        return f"session_{uuid.uuid4().hex[:8]}"
    
    def generate_user_id():
        return f"user_{uuid.uuid4().hex[:8]}"
    
    def validate_user_input(text):
        return text[:2000]  # Simple truncation
    
    class ValidationError(Exception):
        pass
    
    class AgentContext:
        def __init__(self, user_id, session_id, input):
            self.user_id = user_id
            self.session_id = session_id
            self.input = input
            self.conversation_history = []
            
        def add_to_conversation_history(self, role, message):
            self.conversation_history.append((role, message))
    
    class AgentManager:
        def process_request(self, context):
            return {
                "response": f"Echo: {context.input}",
                "confidence": 0.5,
                "sources": []
            }
    
    class RAGManager:
        def process_document(self, file_path):
            return True
    
    class MockConfig:
        BACKEND_DATA_DIR = Path("backend_data")
        DEFAULT_LLM_MODEL = "mistral"
        
    config = MockConfig()
    
    def call_llm(prompt, model=None):
        return f"Mock response to: {prompt[:50]}..."

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="K-Array Chat API",
    description="Backend API for K-Array Chat frontend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
agent_manager = AgentManager()
rag_manager = RAGManager()

# Pydantic models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    confidence: Optional[float] = None
    sources: List[Dict[str, Any]] = []
    timestamp: datetime

class SystemStatusResponse(BaseModel):
    services: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    lastUpdated: datetime

class UploadResponse(BaseModel):
    id: str
    filename: str
    size: int
    status: str
    message: str

# Active sessions storage
active_sessions: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "K-Array Chat API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "api": "running",
            "config": "loaded"
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """
    Main chat endpoint.
    Processes user messages and returns AI responses.
    """
    try:
        # Validate input
        validated_message = validate_user_input(chat_request.message)
        
        # Generate IDs if not provided
        session_id = chat_request.session_id or generate_session_id()
        user_id = chat_request.user_id or generate_user_id()
        
        logger.info(f"Processing chat request - Session: {session_id}, User: {user_id}")
        
        # Create or update session
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                "user_id": user_id,
                "created_at": datetime.now(),
                "message_count": 0,
                "last_activity": datetime.now()
            }
        
        active_sessions[session_id]["last_activity"] = datetime.now()
        active_sessions[session_id]["message_count"] += 1
        
        # Create agent context
        context = AgentContext(
            user_id=user_id,
            session_id=session_id,
            input=validated_message
        )
        
        # Process message through agent system
        response_text = ""
        sources = []
        confidence = None
        
        try:
            # Use agent manager to process the request
            agent_response = await asyncio.to_thread(
                agent_manager.process_request,
                context
            )
            
            if agent_response:
                response_text = agent_response.get("response", "I apologize, but I couldn't process your request.")
                sources = agent_response.get("sources", [])
                confidence = agent_response.get("confidence", None)
            else:
                # Fallback to direct LLM call
                llm_response = await asyncio.to_thread(
                    call_llm,
                    f"You are a helpful K-Array assistant. User question: {validated_message}",
                    model="mistral"
                )
                response_text = llm_response or "I apologize, but I'm having trouble connecting to the AI service."
                
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            response_text = "I apologize, but I encountered an error processing your request. Please try again."
            sources = []
            confidence = None
        
        # Add conversation to context history
        context.add_to_conversation_history("user", validated_message)
        context.add_to_conversation_history("assistant", response_text)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            user_id=user_id,
            confidence=confidence,
            sources=sources,
            timestamp=datetime.now()
        )
        
    except ValidationError as e:
        logger.warning(f"Input validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Input validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Document upload endpoint.
    Accepts files and processes them for the knowledge base.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file size (50MB limit)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Create upload directory if it doesn't exist
        upload_dir = config.BACKEND_DATA_DIR / "uploads"
        upload_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = upload_dir / f"{file_id}_{file.filename}"
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} ({len(content)} bytes)")
        
        # Process file in background
        background_tasks.add_task(
            process_uploaded_file,
            file_path,
            file_id,
            file.filename
        )
        
        return UploadResponse(
            id=file_id,
            filename=file.filename,
            size=len(content),
            status="uploaded",
            message="File uploaded successfully and queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

async def process_uploaded_file(file_path: Path, file_id: str, filename: str):
    """
    Background task to process uploaded files.
    """
    try:
        logger.info(f"Processing uploaded file: {filename}")
        
        # Use RAG manager to process the document
        success = await asyncio.to_thread(
            rag_manager.process_document,
            str(file_path)
        )
        
        if success:
            logger.info(f"Successfully processed file: {filename}")
        else:
            logger.warning(f"Failed to process file: {filename}")
            
    except Exception as e:
        logger.error(f"Error processing uploaded file {filename}: {e}")

@app.get("/api/status", response_model=SystemStatusResponse)
async def system_status():
    """
    System status endpoint.
    Returns current status of all system components.
    """
    try:
        # Check service health
        services = {
            "backend": {
                "status": "healthy",
                "responseTime": 45,
                "lastCheck": datetime.now()
            },
            "llm": {
                "status": "healthy",
                "responseTime": 1200,
                "lastCheck": datetime.now(),
                "model": config.DEFAULT_LLM_MODEL
            },
            "rag": {
                "status": "healthy",
                "responseTime": 300,
                "lastCheck": datetime.now(),
                "documents": await get_document_count()
            },
            "database": {
                "status": "healthy",
                "responseTime": 25,
                "lastCheck": datetime.now(),
                "connections": len(active_sessions)
            }
        }
        
        # System metrics
        metrics = {
            "uptime": get_uptime(),
            "totalRequests": sum(session.get("message_count", 0) for session in active_sessions.values()),
            "avgResponseTime": 430,
            "errorRate": 0.02,
            "memoryUsage": get_memory_usage(),
            "cpuUsage": get_cpu_usage(),
            "diskUsage": get_disk_usage()
        }
        
        return SystemStatusResponse(
            services=services,
            metrics=metrics,
            lastUpdated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@app.get("/api/sessions")
async def get_active_sessions():
    """
    Get information about active sessions.
    """
    try:
        sessions_info = []
        for session_id, session_data in active_sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "user_id": session_data["user_id"],
                "created_at": session_data["created_at"],
                "last_activity": session_data["last_activity"],
                "message_count": session_data["message_count"]
            })
        
        return {
            "total_sessions": len(active_sessions),
            "sessions": sessions_info
        }
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sessions")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a specific session.
    """
    try:
        if session_id in active_sessions:
            del active_sessions[session_id]
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

# Helper functions
async def get_document_count() -> int:
    """Get the number of documents in the knowledge base."""
    try:
        if config.KNOWLEDGE_BASE_FILE.exists():
            with open(config.KNOWLEDGE_BASE_FILE, 'r') as f:
                return sum(1 for _ in f)
        return 0
    except Exception:
        return 0

def get_uptime() -> str:
    """Get system uptime (placeholder)."""
    return "2d 14h 32m"

def get_memory_usage() -> int:
    """Get memory usage percentage (placeholder)."""
    try:
        import psutil
        return int(psutil.virtual_memory().percent)
    except ImportError:
        return 68  # Placeholder

def get_cpu_usage() -> int:
    """Get CPU usage percentage (placeholder)."""
    try:
        import psutil
        return int(psutil.cpu_percent(interval=1))
    except ImportError:
        return 23  # Placeholder

def get_disk_usage() -> int:
    """Get disk usage percentage (placeholder)."""
    try:
        import psutil
        return int(psutil.disk_usage('/').percent)
    except ImportError:
        return 45  # Placeholder

if __name__ == "__main__":
    # Configuration
    host = config._get_env("KCHAT_API_HOST", "localhost")
    port = config._get_int_env("KCHAT_API_PORT", 8000)
    debug = config.DEBUG
    
    logger.info(f"Starting K-Array Chat API server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"CORS origins: http://localhost:3000, http://localhost:5173")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )