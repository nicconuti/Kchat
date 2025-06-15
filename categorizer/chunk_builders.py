"""Utility functions to build retrieval chunks based on document category."""

from __future__ import annotations

from typing import List, Dict, Any


def build_price_chunks(text: str) -> List[Dict[str, str]]:
    """Parse a price table text into structured rows."""
    rows: List[Dict[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("serial"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4 and parts[0].isdigit():
            rows.append(
                {
                    "serial": parts[0],
                    "subcategory": parts[1],
                    "description": parts[2],
                    "price": parts[3],
                }
            )
    return rows


def build_guide_chunks(text: str) -> List[str]:
    """Split guide-like documents into paragraphs."""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def build_chunks(text: str, category: str) -> List[Any]:
    """Dispatch to the correct chunk builder for the given category."""
    if category == "product_price":
        return build_price_chunks(text)
    if category == "product_guide":
        return build_guide_chunks(text)
    return [p.strip() for p in text.split("\n\n") if p.strip()]
