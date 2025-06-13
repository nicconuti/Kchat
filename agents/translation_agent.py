"""Agent for translating text when needed."""

from agents.context import AgentContext
from translator import translate
from utils.logger import get_logger


logger = get_logger("translation_log")


def _auto_correct(text: str) -> str:
    return text.replace(" teh ", " the ").replace("teh ", "the ")


def run(context: AgentContext, target_lang: str, style: str = "neutral") -> AgentContext:
    if context.language == target_lang:
        return context

    corrected = _auto_correct(context.response or context.input)
    translated = translate(corrected, target_lang)
    if style != "neutral":
        translated = f"[{style}] {translated}"
    context.response = translated
    context.language = target_lang
    context.source_reliability = 0.6
    logger.info(f"translated to {target_lang} style={style}")
    logger.info(
        f"reliability={context.source_reliability} error={context.error_flag}"
    )
    return context
