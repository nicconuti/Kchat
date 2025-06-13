"""Perform backend actions (placeholder)."""

from agents.context import AgentContext
from utils.logger import get_logger


logger = get_logger("action_log")


def run(context: AgentContext) -> AgentContext:
    # Example action placeholder
    context.source_reliability = 0.8
    logger.info(f"action for intent {context.intent}")
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
