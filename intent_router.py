"""Intent routing utilities with confidence fallback and expanded intent taxonomy."""

from models.call_local_llm import call_mistral
from config.intents_config import ALLOWED_INTENTS
from typing import Optional

def detect_intent(user_input: str) -> Optional[str]:
    """
    Detect the user's intent using Mistral via Ollama.

    Returns:
        - A valid intent string from ALLOWED_INTENTS if confident.
        - None if the model is unsure or the output is invalid, to trigger a clarification step.
    """

    prompt = (
        "Classify the intent of the following user sentence:\n"
        f"Sentence: \"{user_input}\"\n"
        "Choose and return ONLY ONE of the following categories (no explanation, no punctuation):\n"
        "- technical_support_request → User reports a malfunction and requests help or resolution.\n"
        "- product_information_request → Questions about product features, compatibility, usage.\n"
        "- cost_estimation → Request for pricing or quotation.\n"
        "- booking_or_schedule → Request to schedule appointment, demo, installation.\n"
        "- document_request → Need for manuals, certificates, specs.\n"
        "- open_ticket → User explicitly requests to open a ticket.\n"
        "- complaint → User expresses dissatisfaction, frustration, or criticism without necessarily asking for help.\n"
        "- generic_smalltalk → Greeting or general talk.\n"
        "\n"
        "Use 'technical_support_request' if the message contains a clear request for assistance.\n"
        "Use 'complaint' if the message is primarily a complaint or criticism, even if it mentions a problem.\n"
        "If unclear, return: unclear"
    )

    try:
        response = call_mistral(prompt).strip().lower()
        normalized = response.replace(".", "").replace(",", "").strip()

        if normalized in ALLOWED_INTENTS:
            return normalized
        elif normalized == "unclear":
            return None
        else:
            if (
                " " in normalized
                or "," in normalized
                or normalized not in ALLOWED_INTENTS
            ):
                return None
            return "generic_smalltalk"

    except Exception:
        return None