from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Memory management constants
MAX_CONVERSATION_HISTORY = 50  # Limit conversation history to prevent memory leaks
MAX_DOCUMENTS_PER_CONTEXT = 10  # Limit documents to prevent memory issues
MAX_ACTION_RESULTS = 20  # Limit action results storage


@dataclass
class AgentContext:
    """Shared memory structure passed between agents with memory management."""

    user_id: str
    session_id: str
    input: str
    role: str = "user"
    language: str = "en"
    intent: Optional[str] = None
    confidence: Optional[float] = None
    documents: List[Any] = field(default_factory=list)
    response: Optional[str] = None
    clarification_attempted: bool = False
    formality: Optional[str] = None
    mixed_language: bool = False
    reasoning_trace: str = ""
    source_reliability: float = 0.0
    error_flag: bool = False
    conversation_history: List[Tuple[str, str]] = field(default_factory=list)
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_to_conversation_history(self, role: str, message: str) -> None:
        """Add message to conversation history with memory management."""
        self.conversation_history.append((role, message))
        
        # Trim history if it gets too long
        if len(self.conversation_history) > MAX_CONVERSATION_HISTORY:
            # Keep the most recent messages
            self.conversation_history = self.conversation_history[-MAX_CONVERSATION_HISTORY:]
    
    def add_document(self, document: Any) -> None:
        """Add document with memory management."""
        self.documents.append(document)
        
        # Trim documents if too many
        if len(self.documents) > MAX_DOCUMENTS_PER_CONTEXT:
            self.documents = self.documents[-MAX_DOCUMENTS_PER_CONTEXT:]
    
    def add_action_result(self, result: Dict[str, Any]) -> None:
        """Add action result with memory management."""
        self.action_results.append(result)
        
        # Trim action results if too many
        if len(self.action_results) > MAX_ACTION_RESULTS:
            self.action_results = self.action_results[-MAX_ACTION_RESULTS:]
    
    def clear_context(self, keep_session_info: bool = True) -> None:
        """Clear context data while optionally preserving session info."""
        if not keep_session_info:
            self.user_id = ""
            self.session_id = ""
        
        self.input = ""
        self.intent = None
        self.confidence = None
        self.documents.clear()
        self.response = None
        self.clarification_attempted = False
        self.reasoning_trace = ""
        self.source_reliability = 0.0
        self.error_flag = False
        self.action_results.clear()
        # Keep conversation_history for context
