from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class AgentContext:
    """Shared memory structure passed between agents."""

    user_id: str
    session_id: str
    input: str
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
