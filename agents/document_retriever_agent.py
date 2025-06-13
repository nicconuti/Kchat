"""Retrieve relevant document chunks."""

from agents.context import AgentContext
from utils.logger import get_logger
from typing import Optional

DOCS = {
    "manual": ["manual section 1", "manual section 2"],
    "setup": ["setup guide"],
}


def _retrieve(query: str) -> list[str]:
    for key, docs in DOCS.items():
        if key in query.lower():
            return docs
    return []


logger = get_logger("retrieval_log")


def run(context: AgentContext, query: Optional[str] = None) -> AgentContext:
    if context.user_id == "guest":
        context.error_flag = True
        logger.info("permission denied")
        return context

    docs = _retrieve(query or context.input)
    context.documents = docs
    context.source_reliability = 0.9 if docs else 0.5
    logger.info(f"retrieved {len(context.documents)} docs")
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
