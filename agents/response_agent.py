"""Generate the final response for the user."""

from agents.context import AgentContext
from agents.action_agent import run as action_run
from openchat_worker import generate_response
from utils.logger import get_logger


logger = get_logger("chat_log")


def run(context: AgentContext) -> AgentContext:
    style = context.formality or "neutral"
    if context.documents:
        context.response = f"[{style}] Doc info: {context.documents[0]}"
        context.source_reliability = 0.9
        mode = "doc"
    elif context.intent in {"open_ticket", "cost_estimation"}:
        action_run(context)
        context.response = f"[{style}] Action taken for {context.intent}"
        context.source_reliability = 0.8
        mode = "action"
    else:
        history_lines = [f"{role}:{msg}" for role, msg in context.conversation_history[-4:]]
        history = " ".join(history_lines)
        prompt_input = context.input + (" " + history if history else "")
        context.response = generate_response(
            prompt_input, context.intent or "", context.language
        )
        context.source_reliability = 0.5
        mode = "simple"
    logger.info(
        f"{mode}:{context.response}",
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
