"""Validate generated responses."""

from agents.context import AgentContext
from verifier import verify_response
from utils.logger import get_logger


logger = get_logger("validation_log")


def run(context: AgentContext) -> bool:
    votes = [verify_response(context.input, context.response or "") for _ in range(3)]
    positive = sum(votes)
    if positive >= 2:
        result = True
        classification = "valid"
    elif positive == 1:
        result = False
        classification = "uncertain"
    else:
        result = False
        classification = "invalid"
    context.error_flag = classification == "invalid"
    logger.info(
        classification,
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return result
