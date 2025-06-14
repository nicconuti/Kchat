from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .entity_extractor import extract_entities

CATEGORIES = {
    "tech_assistance": ["errore", "problema", "supporto", "assistenza"],
    "software_assistance": ["software", "installazione", "aggiornamento"],
    "product_price": ["prezzo", "costo", "preventivo", "quote"],
    "product_guide": ["manuale", "guida", "istruzioni"],
}

STOPWORDS = {
    "the",
    "and",
    "a",
    "an",
    "of",
    "for",
    "to",
    "in",
    "il",
    "la",
    "e",
    "un",
    "una",
    "di",
    "per",
    "da",
    "con",
    "non",
    "lo",
    "ho",
    "che",
    "c",
    "funziona",
}


def score(text: str, keywords: list[str]) -> int:
    text_l = text.lower()
    return sum(1 for kw in keywords if kw in text_l)


def extract_subcategories(text: str, max_terms: int = 5) -> list[str]:
    tokens = re.findall(r"[\w'-]{3,}", text.lower())
    filtered = [t for t in tokens if t not in STOPWORDS and not t.isdigit()]
    counts = Counter(filtered)
    frequent = [w for w, _ in counts.most_common(max_terms)]
    try:
        entities = extract_entities(text)
    except Exception:
        entities = []
    combined = frequent + entities
    dedup: list[str] = []
    seen: set[str] = set()
    for token in combined:
        norm = token.lower()
        if norm not in seen:
            seen.add(norm)
            dedup.append(token)
        if len(dedup) >= max_terms:
            break
    return dedup


def classify(text: str, filename: str) -> tuple[str | None, list[str], float, bool]:
    combined = f"{Path(filename).stem} {text}".lower()
    scores = {cat: score(combined, words) for cat, words in CATEGORIES.items()}
    best = max(scores, key=lambda c: scores[c])
    max_score = scores[best]
    sorted_scores = sorted(scores.values(), reverse=True)
    confidence = 0.0 if max_score == 0 else max_score / (sorted_scores[1] + 1)
    ambiguous = max_score == 0 or (len(sorted_scores) > 1 and max_score == sorted_scores[1])
    subcats = extract_subcategories(text)
    return (best if max_score > 0 else None), subcats, 0.5 + confidence / 2, ambiguous
