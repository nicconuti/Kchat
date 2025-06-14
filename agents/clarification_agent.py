"""Ask the user for clarification when needed."""

from pathlib import Path

from agents.context import AgentContext
from clarification_prompt import generate_fallback_question, generate_contextual_question
from utils.logger import get_logger
from typing import Optional


logger = get_logger("clarification_log")
HISTORY_FILE = Path("logs") / "clarification_log.log"


def _most_common_question() -> Optional[str]:
    if not HISTORY_FILE.exists():
        return None
    counts: dict[str, int] = {}
    for line in HISTORY_FILE.read_text().splitlines():
        q = line.split(" - ")[-1]
        counts[q] = counts.get(q, 0) + 1
    if counts:
        return max(counts, key=lambda k: counts[k])
    return None


def run(context: AgentContext) -> AgentContext:
    """Populate ``context.response`` with a context-aware clarification question."""

    # Generate a new question using all available context
    try:
        question = generate_contextual_question(context)
    except Exception:
        question = None

    # Fall back to simpler question generation
    if not question:
        try:
            question = generate_fallback_question(context.input)
        except Exception:
            question = None

    # If everything fails, use a historical or default message
    if not question:
        question = _most_common_question() or "Could you clarify your request?"
    if context.formality == "formal":
        question = f"Gentile utente, {question}"
    context.response = question
    context.clarification_attempted = True
    logger.info(
        question,
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
