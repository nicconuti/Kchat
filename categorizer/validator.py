from __future__ import annotations

import os
from typing import Tuple, List
from utils.logger import get_json_logger
from models.mistral import call_mistral

logger = get_json_logger("validator_log")


def _ask_frontier_llm(text: str) -> Tuple[str | None, List[str], float]:
    """Attempt FRONTIER LLM classification, return category, subcats and confidence."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, [], 0.0
    try:
        import openai

        openai.api_key = api_key
        resp = openai.ChatCompletion.create(  # type: ignore[attr-defined]
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Classify the text"},
                {"role": "user", "content": text},
            ],
        )
        content = resp.choices[0].message.content or ""
        parts = [p.strip() for p in content.split("|")]
        cat = parts[0] if parts else None
        subs = parts[1].split(",") if len(parts) > 1 else []
        return cat, [s.strip() for s in subs if s.strip()], 0.9
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("llm error", extra={"error": repr(exc)})
    return None, [], 0.0

def _ask_llm(text: str) -> Tuple[str | None, List[str], float]:
    """Attempt LOCAL LLM classification, return category, subcats and confidence."""
    try:
        prompt = (
            "You are a document classifier.\n"
            "Given a user input, return the main category and optionally a list of subcategories.\n"
            "Respond in the format: category | subcat1, subcat2, ... (no extra text).\n\n"
            f"Text: \"{text}\"\n"
            "Output:"
        )
        raw = call_mistral(prompt).strip()
        parts = [p.strip() for p in raw.split("|")]
        cat = parts[0] if parts else None
        subs = parts[1].split(",") if len(parts) > 1 else []
        return cat, [s.strip() for s in subs if s.strip()], 0.85
    except Exception as exc:
        logger.error("local_llm_error", extra={"error": repr(exc)})
        return None, [], 0.0


def confirm(
    category: str | None,
    subcats: List[str],
    text: str,
    filename: str,
    *,
    mode: str = "interactive",
    confidence: float,
) -> tuple[str | None, List[str], bool, str, float]:
    """Return possibly adjusted classification and validation status."""
    source = "keyword"
    validated = False
    if mode == "silent":
        return category, subcats, validated, source, confidence

    if (confidence < 0.8 or category is None) and mode != "silent":
        llm_cat, llm_sub, llm_conf = _ask_llm(text)
        if llm_cat and llm_conf >= 0.8:
            category, subcats, confidence = llm_cat, llm_sub, llm_conf
            source = "LLM"
            validated = True
            if mode == "auto":
                return category, subcats, validated, source, confidence

    if mode == "auto" and confidence >= 0.9 and category:
        validated = True
        return category, subcats, validated, source, confidence

    # interactive path
    print(f"Ambiguous classification for {filename} (guess: {category})")
    answer = input("Accept classification? [y/n]: ").strip().lower()
    if answer != "y":
        category = input("Enter category: ") or category
        subs = input("Enter comma-separated subcategories: ")
        if subs:
            subcats = [s.strip() for s in subs.split(",") if s.strip()]
        source = "human_override"
        confidence = 1.0
        validated = True
    return category, subcats, validated, source, confidence
