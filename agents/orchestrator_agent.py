"""Simple rule-based orchestrator."""

from agents.context import AgentContext
from agents.language_agent import run as detect_language
from agents.intent_agent import run as detect_intent
from agents.document_retriever_agent import run as retrieve
from agents.response_agent import run as generate_response
from agents.clarification_agent import run as clarify
from agents.translation_agent import run as translate
from agents.verification_agent import run as verify
from utils.logger import get_logger


logger = get_logger("orchestration_trace")


def choose_agent_sequence(context: AgentContext):
    if "quote" in context.input.lower():
        context.reasoning_trace = "quote request detected"
        seq = [detect_language, detect_intent, retrieve, generate_response, verify]
    else:
        context.reasoning_trace = "default flow"
        seq = [detect_language, detect_intent, generate_response, verify]
    logger.info(context.reasoning_trace)
    return seq


def run(context: AgentContext) -> AgentContext:
    for step in choose_agent_sequence(context):
        step(context)
        if context.error_flag:
            break

    if context.intent is None:
        clarify(context)
    elif not verify(context):
        clarify(context)

    translate(context, context.language)
    logger.info("orchestration complete")
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
