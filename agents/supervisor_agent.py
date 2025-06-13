"""Analyze logs to provide improvement suggestions."""

from pathlib import Path

from agents.context import AgentContext
from utils.logger import get_logger

logger = get_logger("supervisor_log")

LOG_FILES = [
    Path("logs/intent_log.log"),
    Path("logs/validation_log.log"),
]


def _analyze_intent_log(text: str) -> str | None:
    unclear = text.lower().count("unclear")
    if unclear:
        return f"Improve intent detection: {unclear} unclear cases"
    return None


def _analyze_validation_log(text: str) -> str | None:
    invalid = text.lower().count("invalid")
    if invalid:
        return f"Refine response verification: {invalid} invalid answers"
    return None


def run(context: AgentContext) -> AgentContext:
    suggestions = []
    for path in LOG_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        if "intent" in path.name:
            result = _analyze_intent_log(text)
        elif "validation" in path.name:
            result = _analyze_validation_log(text)
        else:
            result = None
        if result:
            suggestions.append(result)
    context.response = "; ".join(suggestions) if suggestions else "No issues"
    logger.info(context.response)
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
