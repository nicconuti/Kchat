"""Analyze logs to provide improvement suggestions."""

from pathlib import Path

from agents.context import AgentContext
from utils.logger import get_logger

logger = get_logger("supervisor_log")

LOG_FILES = [
    Path("logs/intent_log.log"),
    Path("logs/validation_log.log"),
]


def run(context: AgentContext) -> AgentContext:
    suggestions = []
    for path in LOG_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        errors = text.count("False") + text.count("unclear")
        if errors:
            suggestions.append(f"Review {path.name}: {errors} issues")
    context.response = "; ".join(suggestions) if suggestions else "No issues"
    logger.info(
        context.response,
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
