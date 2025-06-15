from __future__ import annotations

import os
from typing import Tuple, List
from utils.logger import get_json_logger
from models.mistral import call_mistral

logger = get_json_logger("validator_log")


def parse_llm_output(raw: str) -> Tuple[str | None, List[str]]:
    """Parse output in the format: MainCategory | Subcat1, Subcat2"""
    parts = [p.strip() for p in raw.split("|")]
    cat = parts[0] if parts else None
    subs = parts[1].split(",") if len(parts) > 1 else []
    subcats = [s.strip() for s in subs if s.strip()]
    return cat, subcats


def _ask_frontier_llm(text: str) -> Tuple[str | None, List[str], float]:
    """Attempt FRONTIER LLM classification using OpenAI."""
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
        cat, subcats = parse_llm_output(content)
        return cat, subcats, 0.9
    except Exception as exc:
        logger.error("llm_error", extra={"error": repr(exc)})
        return None, [], 0.0


def _ask_llm(text: str) -> Tuple[str | None, List[str], float]:
    """Attempt LOCAL LLM classification via Mistral."""
    prompt = (
        "Classify the following document into:\n"
        "- One main category (CamelCase, required)\n"
        "- Optional subcategories (CamelCase, comma-separated)\n\n"
        "⚠️ Output format (strict, no deviation):\n"
        "MainCategory | Subcat1, Subcat2\n"
        "If no subcategories, leave empty after pipe (e.g. 'ProductManual |')\n"
        "If unclassifiable, return: Uncategorized |\n\n"
        f"Document:\n{text[:1000]}\n\n"
        "Answer:\n"
        "Valid categories: TechSupport, SoftwareAssistance, ProductManual, ProductPrice, Documentation, Uncategorized"
    )

    try:
        raw = call_mistral(prompt).strip()
        cat, subcats = parse_llm_output(raw)
        if cat is None:
            logger.warning("unparsable_llm_output", extra={"raw": raw})
            return "Uncategorized", [], 0.0
        return cat, subcats, 0.85
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
) -> Tuple[str | None, List[str], bool, str, float]:
    """
    Confirm classification and optionally ask for manual override.

    Returns:
        (final_category, final_subcats, validated, source, confidence)
    """
    source = "keyword"
    validated = False

    if mode == "silent":
        return category, subcats, validated, source, confidence

    if (confidence < 0.9 or category is None) and mode != "silent":
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

    # Interactive fallback
    print(f"Ambiguous classification for {filename} (guess: category - {category} __ sub - {subcats})")
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
