"""Intent routing utilities."""

from models.mistral import call_mistral


ALLOWED_INTENTS = {
    "estimate_costs_and_fees",
    "retrieve_document",
    "open_ticket",
    "schedule_service",
    "generic",
}


def detect_intent(user_input: str) -> str:
    """Detect the user's intent using Mistral via Ollama."""

    prompt = (
        "Classify the intent of the following user sentence:\n"
        f"Sentence: \"{user_input}\"\n"
        "Choose and return ONLY ONE of the following values with no extra text:"
        " estimate_costs_and_fees, retrieve_document, open_ticket, schedule_service, generic."
    )

    raw = call_mistral(prompt).strip().lower()
    # Ensure only a valid intent is returned
    for intent in ALLOWED_INTENTS:
        if intent == raw:
            return intent
    return "generic"
