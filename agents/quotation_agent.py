"""Generate a PDF quote (placeholder implementation)."""

from agents.context import AgentContext
from utils.logger import get_logger


logger = get_logger("quotation_log")


def run(context: AgentContext) -> AgentContext:
    context.response = "Generated quote PDF"  # placeholder
    context.source_reliability = 0.95
    logger.info("quote created")
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
