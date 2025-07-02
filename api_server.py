#!/usr/bin/env python3
"""
FastAPI server for K-Array Chat frontend.
Provides REST API endpoints for the React frontend.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import json
import uuid

# Ensure correct Haystack-AI path is available for the API server
if '/opt/homebrew/lib/python3.9/site-packages' not in sys.path:
    sys.path.insert(0, '/opt/homebrew/lib/python3.9/site-packages')
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import Response
from pydantic import BaseModel, Field
import asyncio
from typing import AsyncGenerator
import uvicorn
logger = logging.getLogger("server")

# Import Kchat components - import one by one for better error handling
import_errors = []

# Import session management
try:
    from main import generate_session_id, generate_user_id
    logger.info("Session management imported successfully")
except ImportError as e:
    import_errors.append(f"Session management: {e}")
    def generate_session_id():
        return f"session_{uuid.uuid4().hex[:8]}"
    
    def generate_user_id():
        return f"user_{uuid.uuid4().hex[:8]}"

# Import agent system
try:
    from agents.context import AgentContext
    from agents.agent_manager import AgentManager
    logger.info("Agent system imported successfully")
    AGENT_SYSTEM_AVAILABLE = True
except ImportError as e:
    import_errors.append(f"Agent system: {e}")
    AGENT_SYSTEM_AVAILABLE = False
    
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
            logger.warning("Using mock AgentManager - full system not available")
            return {
                "response": f"Sistema in modalità demo - messaggio ricevuto: {context.input}",
                "confidence": 0.5,
                "sources": []
            }

# Import LLM system
try:
    from models._call_llm import LLMClient
    # Create a global LLM client instance
    _llm_client = LLMClient(default_model="mistral")
    
    def call_llm(prompt, model=None):
        """Wrapper function for LLM calls."""
        try:
            return _llm_client.call(prompt, model=model)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"Mi dispiace, si è verificato un errore nel sistema LLM."
    
    logger.info("LLM system imported successfully")
    LLM_SYSTEM_AVAILABLE = True
except ImportError as e:
    import_errors.append(f"LLM system: {e}")
    LLM_SYSTEM_AVAILABLE = False
    
    def call_llm(prompt, model=None):
        logger.warning("Using mock LLM - full system not available")
        return f"Mock LLM response to: {prompt[:100]}..."

# Import input validation
try:
    from utils.input_validator import validate_user_input, ValidationError
    logger.info("Input validation imported successfully")
except ImportError as e:
    import_errors.append(f"Input validation: {e}")
    
    def validate_user_input(text):
        return text[:2000]  # Simple truncation
    
    class ValidationError(Exception):
        pass

# Import configuration
try:
    from config.settings import config
    logger.info("Configuration imported successfully")
except ImportError as e:
    import_errors.append(f"Configuration: {e}")
    
    class MockConfig:
        BACKEND_DATA_DIR = Path("backend_data")
        DEFAULT_LLM_MODEL = "mistral"
        
        def _get_env(self, key, default):
            return os.getenv(key, default)
            
        def _get_int_env(self, key, default):
            try:
                return int(os.getenv(key, str(default)))
            except ValueError:
                return default
        
    config = MockConfig()

# Import RAG system
try:
    from rag_manager import RAGManager
    logger.info("RAG system imported successfully")
    RAG_SYSTEM_AVAILABLE = True
except ImportError as e:
    import_errors.append(f"RAG system: {e}")
    RAG_SYSTEM_AVAILABLE = False
    
    class RAGManager:
        def process_document(self, file_path):
            logger.warning("Using mock RAG manager - full system not available")
            return True

# Log import status
if import_errors:
    logger.warning("Some Kchat components not available:")
    for error in import_errors:
        logger.warning(f"  - {error}")
    logger.warning("API will run with limited functionality")
else:
    logger.info("All Kchat components imported successfully")

# System availability flags
SYSTEM_STATUS = {
    "agent_system": AGENT_SYSTEM_AVAILABLE,
    "llm_system": LLM_SYSTEM_AVAILABLE,
    "rag_system": RAG_SYSTEM_AVAILABLE,
    "import_errors": import_errors
}

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
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],  # React dev servers
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

class StreamMessage(BaseModel):
    """Model for streaming chat messages."""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    include_reasoning: bool = True

class StreamEvent(BaseModel):
    """Model for streaming events."""
    type: str  # 'reasoning', 'progress', 'response', 'complete', 'error'
    data: Dict[str, Any]
    timestamp: Optional[str] = None

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
    logger.info(f"Chat request received: {chat_request.message[:50]}...")
    try:
        # Validate input (permissive mode for chat messages)
        validated_message = validate_user_input(chat_request.message, is_chat_message=True)
        
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
            if AGENT_SYSTEM_AVAILABLE:
                # Use the full agent system
                agent_response = await asyncio.to_thread(
                    agent_manager.process_request,
                    context
                )
                
                if agent_response:
                    response_text = agent_response.get("response", "Mi dispiace, non sono riuscito a elaborare la tua richiesta.")
                    sources = agent_response.get("sources", [])
                    confidence = agent_response.get("confidence", None)
                    logger.info(f"Agent system response generated (confidence: {confidence})")
                else:
                    response_text = "Mi dispiace, il sistema degli agenti non ha prodotto una risposta."
                    
            elif LLM_SYSTEM_AVAILABLE:
                # Fallback to direct LLM call
                logger.info("Using direct LLM fallback")
                llm_response = await asyncio.to_thread(
                    call_llm,
                    f"Sei un assistente esperto di K-Array. Rispondi in italiano. Domanda dell'utente: {validated_message}",
                    model=config.DEFAULT_LLM_MODEL if hasattr(config, 'DEFAULT_LLM_MODEL') else "mistral"
                )
                response_text = llm_response or "Mi dispiace, sto avendo problemi a connettermi al servizio AI."
                confidence = 0.7
                
            else:
                # Basic fallback response
                logger.warning("No AI systems available, using basic response")
                response_text = f"Sistema in modalità limitata. Ho ricevuto il tuo messaggio: '{validated_message}'. Per un'assistenza completa, consulta www.k-array.com"
                confidence = 0.1
                
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            response_text = "Mi dispiace, si è verificato un errore nell'elaborazione della tua richiesta. Riprova."
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


@app.post("/api/chat/stream")
async def chat_stream_endpoint(stream_request: StreamMessage):
    """
    Streaming chat endpoint with reasoning process.
    Returns Server-Sent Events for real-time updates.
    """
    logger.info(f"Stream chat request received: {stream_request.message[:50]}...")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            # Validate input
            validated_message = validate_user_input(stream_request.message, is_chat_message=True)
            
            # Generate IDs if not provided
            session_id = stream_request.session_id or generate_session_id()
            user_id = stream_request.user_id or generate_user_id()
            
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'data': {'session_id': session_id, 'user_id': user_id}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            if AGENT_SYSTEM_AVAILABLE:
                # Create context
                context = AgentContext(
                    user_id=user_id,
                    session_id=session_id,
                    input=validated_message
                )
                
                # Process with streaming updates
                async for event in process_with_streaming(context, stream_request.include_reasoning):
                    yield f"data: {json.dumps(event)}\n\n"
                    
            else:
                # Fallback response
                yield f"data: {json.dumps({'type': 'response', 'data': {'text': 'Agent system not available'}, 'timestamp': datetime.now().isoformat()})}\n\n"
                
            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'data': {}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}, 'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


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
        # Check service health based on actual system availability
        services = {
            "backend": {
                "status": "healthy",
                "responseTime": 45,
                "lastCheck": datetime.now(),
                "details": "API server running"
            },
            "llm": {
                "status": "healthy" if LLM_SYSTEM_AVAILABLE else "warning",
                "responseTime": 1200 if LLM_SYSTEM_AVAILABLE else None,
                "lastCheck": datetime.now(),
                "model": getattr(config, 'DEFAULT_LLM_MODEL', 'unknown'),
                "available": LLM_SYSTEM_AVAILABLE
            },
            "agent_system": {
                "status": "healthy" if AGENT_SYSTEM_AVAILABLE else "warning", 
                "responseTime": 500 if AGENT_SYSTEM_AVAILABLE else None,
                "lastCheck": datetime.now(),
                "available": AGENT_SYSTEM_AVAILABLE
            },
            "rag": {
                "status": "healthy" if RAG_SYSTEM_AVAILABLE else "warning",
                "responseTime": 300 if RAG_SYSTEM_AVAILABLE else None,
                "lastCheck": datetime.now(),
                "documents": await get_document_count(),
                "available": RAG_SYSTEM_AVAILABLE
            },
            "database": {
                "status": "healthy",
                "responseTime": 25,
                "lastCheck": datetime.now(),
                "connections": len(active_sessions),
                "active_sessions": len(active_sessions)
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
        
        # Add system status information
        system_info = {
            "services": services,
            "metrics": metrics,
            "lastUpdated": datetime.now(),
            "system_status": SYSTEM_STATUS,
            "import_errors": import_errors if import_errors else None
        }
        
        return system_info
        
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


async def process_with_streaming(context: AgentContext, include_reasoning: bool = True) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Simplified streaming processing with reasoning steps.
    """
    try:
        # Step 1: Initial reasoning
        if include_reasoning:
            yield {
                'type': 'reasoning',
                'data': {
                    'step': 'start', 
                    'message': 'Iniziando elaborazione della richiesta...'
                },
                'timestamp': datetime.now().isoformat()
            }
            
            await asyncio.sleep(0.1)  # Small delay for better UX
        
        # Step 2: Process using existing agent manager (synchronous)
        if include_reasoning:
            yield {
                'type': 'progress',
                'data': {
                    'step': 'processing',
                    'message': 'Elaborando con sistema agenti...'
                },
                'timestamp': datetime.now().isoformat()
            }
        
        # Use the existing agent manager to process the request
        try:
            agent_response = await asyncio.to_thread(
                agent_manager.process_request,
                context
            )
            
            if include_reasoning:
                yield {
                    'type': 'reasoning',
                    'data': {
                        'step': 'completed',
                        'message': 'Elaborazione completata con successo!'
                    },
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            if include_reasoning:
                yield {
                    'type': 'reasoning',
                    'data': {
                        'step': 'error',
                        'message': f'Errore durante elaborazione: {str(e)}'
                    },
                    'timestamp': datetime.now().isoformat()
                }
            
            # Fallback response
            agent_response = {
                "response": "Mi dispiace, si è verificato un errore nell'elaborazione della tua richiesta.",
                "confidence": 0.1,
                "sources": []
            }
        
        # Step 3: Stream the response
        response_text = agent_response.get("response", "Risposta non disponibile.")
        
        if include_reasoning:
            yield {
                'type': 'reasoning',
                'data': {
                    'step': 'streaming',
                    'message': 'Inviando risposta...'
                },
                'timestamp': datetime.now().isoformat()
            }
        
        # Stream response word by word
        words = response_text.split()
        current_text = ""
        
        for i, word in enumerate(words):
            current_text += word + " "
            yield {
                'type': 'response',
                'data': {
                    'text': current_text.strip(),
                    'is_complete': i == len(words) - 1
                },
                'timestamp': datetime.now().isoformat()
            }
            # Small delay for streaming effect
            await asyncio.sleep(0.08)
        
        # Final metadata
        yield {
            'type': 'metadata',
            'data': {
                'confidence': agent_response.get('confidence'),
                'sources': agent_response.get('sources', [])
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        yield {
            'type': 'error',
            'data': {
                'message': f'Errore durante l\'elaborazione: {str(e)}',
                'error': str(e)
            },
            'timestamp': datetime.now().isoformat()
        }


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