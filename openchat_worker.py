from typing import Iterator

from models.call_local_llm import call_openchat, stream_openchat


def generate_response(user_input: str, intent: str, lang: str) -> str:
    """Generate a helpful answer using OpenChat.

    The assistant is instructed to reply in the same language as the
    user's message.
    """

    prompt = (
        f"The user asked: {user_input}\n"
        f"Detected intent: {intent}.\n"
        f"Reply in language: {lang}.\n"
        "Provide a clear, helpful response."
    )
    return call_openchat(prompt)


def generate_response_stream(user_input: str, intent: str, lang: str) -> Iterator[str]:
    """Stream a response from OpenChat."""
    prompt = (
        f"The user asked: {user_input}\n"
        f"Detected intent: {intent}.\n"
        f"Reply in language: {lang}.\n"
        "Provide a clear, helpful response."
    )
    return stream_openchat(prompt)
