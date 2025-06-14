"""Analyze logs to provide improvement suggestions."""

from pathlib import Path

from agents.context import AgentContext
from utils.logger import get_logger
from models.mistral import call_mistral

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


def _collect_snippets() -> str:
    snippets = []
    for path in LOG_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        snippets.append(f"## {path.name}\n{text[-500:]}")
    return "\n\n".join(snippets)


def run(context: AgentContext) -> AgentContext:
    prompts = _collect_snippets()
    prompt = (
        "You are a supervisor agent analyzing logs to suggest improvements. "
        "Provide short, actionable recommendations.\n" + prompts + "\nSuggestions:"
    )
    try:
        suggestion = call_mistral(prompt).strip()
    except Exception:
        suggestion = ""

    if not suggestion:
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
        suggestion = "; ".join(suggestions) if suggestions else "No issues"

    context.response = suggestion
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
