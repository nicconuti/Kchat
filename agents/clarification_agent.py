"""Ask the user for clarification when needed."""

from pathlib import Path

from agents.context import AgentContext
from clarification_prompt import generate_fallback_question
from utils.logger import get_logger


logger = get_logger("clarification_log")
HISTORY_FILE = Path("logs") / "clarification_log.log"


def _most_common_question() -> str | None:
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
    question = _most_common_question() or generate_fallback_question(context.input)
    if context.formality == "formal":
        question = f"Gentile utente, {question}"
    context.response = question
    context.clarification_attempted = True
    logger.info(question)
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
