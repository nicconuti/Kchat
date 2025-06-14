"""Fallback question generator using Mistral for clarification when intent is unclear."""

from models.mistral import call_mistral
from config.intents_config import ALLOWED_INTENTS
from language_detector import detect_language
from agents.context import AgentContext

def generate_fallback_question(user_input: str) -> str:
    """
    Given a user input that failed intent classification, use Mistral to generate
    a clarification question that helps narrow down the user's intent.

    Args:
        user_input (str): The original input from the user.

    Returns:
        str: A question that prompts the user to clarify their request.
    """

    lang = detect_language(user_input)
    intent_list = ", ".join(sorted(ALLOWED_INTENTS))

    prompt = (
        f"You are an AI assistant that replies in the same language as the user's message (detected language: {lang}).\n"
        "The user's message was ambiguous and the system could not determine the intent.\n"
        "Generate ONE short, precise, natural-sounding follow-up question to clarify what the user wants.\n"
        f"The goal is to distinguish between intents such as: {intent_list}.\n"
        "Your response must be ONLY the question, in the same language as the user.\n"
        f"\nUser message: \"{user_input}\"\n"
        "\nClarification question:"
    )

    try:
        return call_mistral(prompt).strip()
    except Exception:
        fallback_prompt = (
            f"Translate the following sentence into {lang}: 'Could you clarify your request?'"
        )
        return call_mistral(fallback_prompt).strip()


def generate_contextual_question(context: AgentContext) -> str:
    """Generate a clarification question using extra context."""

    lang = context.language or detect_language(context.input)
    intent_list = ", ".join(sorted(ALLOWED_INTENTS))
    reasoning = context.reasoning_trace or ""
    prev_answer = context.response or ""
    history_lines = []
    for role, msg in context.conversation_history[-4:]:
        history_lines.append(f"{role.capitalize()}: {msg}")
    history = "\n".join(history_lines)

    prompt = (
        f"You are an AI assistant that replies in the same language as the user's message (detected language: {lang}).\n"
        "The user's intent was unclear and a clarification is required.\n"
        f"System reasoning so far: {reasoning}\n"
        f"Current system answer: {prev_answer}\n"
        + (f"Conversation so far:\n{history}\n" if history else "")
        + f"Generate ONE short, precise follow-up question to clarify the request.\n"
        f"Possible intents include: {intent_list}.\n"
        f"\nUser message: \"{context.input}\"\n"
        "\nClarification question:"
    )

    try:
        return call_mistral(prompt).strip()
    except Exception:
        fallback_prompt = (
            f"Translate the following sentence into {lang}: 'Could you clarify your request?'"
        )
        return call_mistral(fallback_prompt).strip()
