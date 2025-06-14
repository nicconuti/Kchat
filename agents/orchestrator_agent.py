"""Simple rule-based orchestrator."""

from agents.context import AgentContext
from agents.language_agent import run as detect_language
from agents.intent_agent import run as detect_intent
from agents.document_retriever_agent import run as retrieve
from agents.response_agent import run as generate_response
from agents.clarification_agent import run as clarify
from agents.translation_agent import run as translate
from translator import translate as translate_text
from agents.verification_agent import run as verify
from models.mistral import call_mistral
from utils.logger import get_logger
import json


logger = get_logger("orchestration_trace")


_STEP_MAP = {
    "language": detect_language,
    "intent": detect_intent,
    "retrieve": retrieve,
    "respond": generate_response,
    "clarify": clarify,
}


def _fallback_sequence(context: AgentContext):
    if "quote" in context.input.lower():
        seq = ["language", "intent", "retrieve", "respond"]
        reasoning = "fallback: quote request"
    else:
        seq = ["language", "intent", "respond"]
        reasoning = "fallback: default"
    return reasoning, [
        _STEP_MAP[name] for name in seq if name in _STEP_MAP
    ]


def choose_agent_sequence(context: AgentContext):
    prompt = (
        "You are an orchestrator deciding which agents to run."
        " Available agents: language, intent, retrieve, respond."
        " Based on the user message, output a JSON object with keys"
        " 'reasoning' (string) and 'sequence' (list of agent names)."
        f" User message: {context.input!r}\nJSON:"
    )

    try:
        raw = call_mistral(prompt)
        data = json.loads(raw)
        context.reasoning_trace = data.get("reasoning", "")
        seq_names = data.get("sequence", [])
        seq = [_STEP_MAP.get(n) for n in seq_names if n in _STEP_MAP]
        if not seq:
            raise ValueError("empty sequence")
    except Exception:
        context.reasoning_trace, seq = _fallback_sequence(context)

    logger.info(
        context.reasoning_trace,
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )

    return seq



def run(context: AgentContext) -> AgentContext:
    original_input = context.input
    for step in choose_agent_sequence(context):
        if step is detect_intent:
            pivot_text = (
                translate_text(context.input, "en")
                if context.language != "en"
                else context.input
            )
            context.input = pivot_text
            step(context)
            context.input = original_input
        else:
            step(context)
        if context.error_flag:
            break

    if context.intent is None:
        clarify(context)
    elif not verify(context):
        clarify(context)

    translate(context, context.language)
    logger.info(
        "orchestration complete",
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
