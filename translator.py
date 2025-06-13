"""Utility for translating text using the local LLM."""

from typing import Iterator

from models.mistral import call_mistral, stream_mistral


def translate(text: str, target_lang: str = "en") -> str:
    """Translate ``text`` to ``target_lang`` using Mistral.

    Args:
        text: The text to translate.
        target_lang: Two letter ISO code of the desired language.

    Returns:
        The translated text. If translation fails, the original text
        is returned unchanged.
    """

    prompt = (
        f"Translate the following text to {target_lang}.\n"
        "Return only the translated sentence without explanations.\n"
        f"Text: {text}\n"
        "Translated text:"
    )

    try:
        return call_mistral(prompt).strip()
    except Exception:
        return text


def translate_stream(text: str, target_lang: str = "en") -> Iterator[str]:
    """Stream translated text token by token."""
    prompt = (
        f"Translate the following text to {target_lang}.\n"
        "Return only the translated sentence without explanations.\n"
        f"Text: {text}\n"
        "Translated text:"
    )
    try:
        yield from stream_mistral(prompt)
    except Exception:
        yield text
