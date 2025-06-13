"""Agent responsible for detecting the language of the user input."""

from agents.context import AgentContext
from language_detector import detect_language
from utils.logger import get_logger

FORMAL_WORDS = ["gentile", "salve", "buongiorno", "distinti"]
INFORMAL_WORDS = ["ciao", "hey", "hola"]


def speech_to_text(audio_path: str) -> str:
    """Dummy speech-to-text hook."""
    return "transcribed"


logger = get_logger("lang_log")


def _detect_formality(text: str) -> str:
    text_l = text.lower()
    if any(w in text_l for w in FORMAL_WORDS):
        return "formal"
    if any(w in text_l for w in INFORMAL_WORDS):
        return "informal"
    return "neutral"


def _mixed_language(text: str) -> bool:
    return any(word in text.lower() for word in ["hello", "ciao", "hola"]) and (
        "ciao" in text.lower() and "hello" in text.lower()
    )


def run(context: AgentContext) -> AgentContext:
    text = context.input
    if text.endswith(('.wav', '.mp3')):
        text = speech_to_text(text)
        context.input = text

    lang = detect_language(text)
    context.language = lang
    context.formality = _detect_formality(text)
    context.mixed_language = _mixed_language(text)
    context.source_reliability = 0.7
    logger.info(f"{lang} {context.formality} mixed={context.mixed_language}")
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
