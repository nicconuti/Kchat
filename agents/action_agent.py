"""Perform backend actions (placeholder)."""

from agents.context import AgentContext
from utils.logger import get_logger


logger = get_logger("action_log")


def run(context: AgentContext) -> AgentContext:
    # Example action placeholder
    context.source_reliability = 0.8
    logger.info(
        f"action for intent {context.intent}",
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
