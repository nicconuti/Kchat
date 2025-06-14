from __future__ import annotations

from functools import lru_cache
from typing import List

import spacy


@lru_cache(maxsize=1)
def _get_nlp() -> spacy.language.Language:
    """Load and cache the multilingual NER model."""
    try:
        return spacy.load("xx_ent_wiki_sm")
    except OSError:
        from spacy.cli import download

        download("xx_ent_wiki_sm")
        return spacy.load("xx_ent_wiki_sm")


def extract_entities(text: str) -> List[str]:
    """Return product or software names detected via NER."""
    nlp = _get_nlp()
    doc = nlp(text)
    entities: List[str] = []
    seen: set[str] = set()
    for ent in doc.ents:
        if ent.label_ in {"ORG", "MISC", "PRODUCT", "WORK_OF_ART"}:
            val = ent.text.strip()
            if val and val.lower() not in seen:
                seen.add(val.lower())
                entities.append(val)
    return entities
