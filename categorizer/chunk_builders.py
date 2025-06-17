"""Utility functions to build retrieval chunks based on document category."""

from __future__ import annotations

from typing import List,  Any
from categorizer.price_chunk_builder import parse_price_table

def build_guide_chunks(text: str) -> List[str]:
    """Split guide-like documents into paragraphs."""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def build_chunks(text: str, category: str) -> List[Any]:
    """Dispatch to the correct chunk builder for the given category."""
    if category == "product_price":
        return parse_price_table(text)
    if category == "product_guide":
        return build_guide_chunks(text)
    return [p.strip() for p in text.split("\n\n") if p.strip()]
