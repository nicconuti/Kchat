"""
Agent Manager for coordinating the multi-agent pipeline.
Provides a simplified interface for the API server.
"""

import logging
from typing import Dict, Any, Optional
from agents.context import AgentContext
from agents.orchestrator_agent import run as orchestrator_run
from utils.logger import get_logger

logger = get_logger("agent_manager")

class AgentManager:
    """
    Manager class for coordinating the K-Array multi-agent system.
    Provides a simplified interface for processing user requests.
    """
    
    def __init__(self):
        """Initialize the agent manager."""
        self.logger = logger
        self.logger.info("AgentManager initialized")
    
    def process_request(self, context: AgentContext) -> Optional[Dict[str, Any]]:
        """
        Process a user request through the multi-agent pipeline.
        
        Args:
            context: AgentContext containing user input and session information
            
        Returns:
            Dictionary containing response, sources, and confidence information
        """
        try:
            self.logger.info(f"Processing request for session {context.session_id}")
            
            # Run the orchestrator pipeline
            processed_context = orchestrator_run(context)
            
            # Extract response information
            response_data = {
                "response": processed_context.response or "Mi dispiace, non sono riuscito a elaborare la tua richiesta.",
                "confidence": getattr(processed_context, 'confidence', None),
                "source_reliability": getattr(processed_context, 'source_reliability', None),
                "sources": self._extract_sources(processed_context),
                "intent": getattr(processed_context, 'intent', None),
                "language": getattr(processed_context, 'language', 'it'),
                "error_flag": getattr(processed_context, 'error_flag', False),
                "reasoning_trace": getattr(processed_context, 'reasoning_trace', None)
            }
            
            # Log processing completion
            self.logger.info(
                f"Request processed successfully for session {context.session_id}",
                extra={
                    "response_length": len(response_data["response"]),
                    "confidence": response_data["confidence"],
                    "source_reliability": response_data["source_reliability"],
                    "sources_count": len(response_data["sources"]),
                    "error_flag": response_data["error_flag"]
                }
            )
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            
            # Return fallback response
            return {
                "response": "Mi dispiace, si è verificato un errore interno. Ti preghiamo di riprovare.",
                "confidence": 0.0,
                "source_reliability": 0.0,
                "sources": [],
                "intent": None,
                "language": "it",
                "error_flag": True,
                "reasoning_trace": f"Error in agent pipeline: {str(e)}"
            }
    
    def _extract_sources(self, context: AgentContext) -> list:
        """
        Extract source information from the processed context.
        
        Args:
            context: Processed AgentContext
            
        Returns:
            List of source dictionaries
        """
        sources = []
        
        try:
            # Extract from documents if available
            if hasattr(context, 'documents') and context.documents:
                for doc in context.documents:
                    if isinstance(doc, dict):
                        source_info = {
                            "title": doc.get("title", "Document"),
                            "url": doc.get("url", ""),
                            "snippet": doc.get("content", "")[:200] + "..." if doc.get("content") else "",
                            "confidence": doc.get("score", 0.0),
                            "type": doc.get("type", "document")
                        }
                        sources.append(source_info)
                    else:
                        # Handle string documents
                        sources.append({
                            "title": "Document",
                            "url": "",
                            "snippet": str(doc)[:200] + "..." if len(str(doc)) > 200 else str(doc),
                            "confidence": 0.5,
                            "type": "document"
                        })
            
            # Extract from action results if available
            if hasattr(context, 'action_results') and context.action_results:
                for result in context.action_results:
                    if isinstance(result, dict) and result.get("type") == "source":
                        sources.append({
                            "title": result.get("title", "Action Result"),
                            "url": result.get("url", ""),
                            "snippet": result.get("content", "")[:200] + "..." if result.get("content") else "",
                            "confidence": result.get("confidence", 0.5),
                            "type": "action"
                        })
        
        except Exception as e:
            self.logger.warning(f"Error extracting sources: {e}")
        
        return sources
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent manager.
        
        Returns:
            Dictionary containing status information
        """
        return {
            "status": "healthy",
            "agent_count": 1,  # Orchestrator manages multiple agents
            "last_check": "now",
            "version": "1.0.0"
        }
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear session-specific data for a given session.
        
        Args:
            session_id: Session ID to clear
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Clearing session data for {session_id}")
            # Session data is typically managed by the context itself
            # This is a placeholder for any session-specific cleanup
            return True
        except Exception as e:
            self.logger.error(f"Error clearing session {session_id}: {e}")
            return False