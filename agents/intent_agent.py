"""Agent for classifying user intent."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from agents.context import AgentContext
from config.intents_config import ALLOWED_INTENTS
from intent_router import detect_intent
from utils.logger import get_logger


logger = get_logger("intent_log")

HISTORY_FILE = Path("logs") / "intent_log.log"

# Basic keyword hints used for rule-based intent detection
KEYWORDS: Dict[str, List[str]] = {
    "technical_support_request": [
        "error",
        "issue",
        "problem",
        "help",
        "doesn't",
        "won't",
    ],
    "product_information_request": [
        "feature",
        "spec",
        "compatibility",
        "information",
        "detail",
    ],
    "cost_estimation": [
        "quote",
        "pricing",
        "price",
        "cost",
        "preventivo",
    ],
    "booking_or_schedule": [
        "schedule",
        "appointment",
        "booking",
        "demo",
        "meeting",
        "install",
    ],
    "document_request": [
        "manual",
        "document",
        "certificate",
        "datasheet",
        "pdf",
    ],
    "open_ticket": ["open ticket", "create ticket", "support ticket"],
    "complaint": [
        "complaint",
        "dissatisfied",
        "disappointed",
        "broken",
        "damaged",
    ],
    "generic_smalltalk": ["hello", "hi", "ciao", "thanks", "thank you"],
}


def _rule_based_intent(text: str) -> Optional[str]:
    """Return an intent based on simple keyword heuristics."""

    text_l = text.lower()
    for intent, words in KEYWORDS.items():
        for w in words:
            if w in text_l:
                return intent
    return None


def _most_frequent_from_logs() -> Optional[str]:
    """Return the most frequent intent observed in previous logs."""

    counts: Dict[str, int] = defaultdict(int)
    if HISTORY_FILE.exists():
        for line in HISTORY_FILE.read_text().splitlines():
            if "-" in line:
                _, _, val = line.partition("-")
                intent = val.strip()
                if intent in ALLOWED_INTENTS:
                    counts[intent] += 1
    if counts:
        return max(counts, key=lambda k: counts[k])
    return None


def run(context: AgentContext) -> AgentContext:
    """Classify user intent with heuristics and LLM fallback."""

    rule_guess = _rule_based_intent(context.input)
    llm_guess = detect_intent(context.input)

    # If LLM produced nothing, fall back to history or rule guess
    if llm_guess is None:
        llm_guess = rule_guess or _most_frequent_from_logs()

    if rule_guess and llm_guess and rule_guess == llm_guess:
        intent = llm_guess
        confidence = 1.0
    elif llm_guess:
        intent = llm_guess
        confidence = 0.9 if rule_guess else 0.8
    elif rule_guess:
        intent = rule_guess
        confidence = 0.6
    else:
        intent = None
        confidence = 0.0

    context.intent = intent
    context.confidence = confidence
    context.source_reliability = confidence
    logger.info(
        intent if intent else "unclear",
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
