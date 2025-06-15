"""Utility functions to build retrieval chunks based on document category."""

from __future__ import annotations

from typing import List, Dict, Any


def build_price_chunks(text: str) -> List[Dict[str, str]]:
    """Parse a price table text into structured rows."""
    rows: List[Dict[str, str]] = []
    sequential: List[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if "|" in line:
            if line.lower().startswith("serial"):
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
        else:
            sequential.append(line)

    if sequential:
        headers = ["serial", "subcategory", "description", "price"]
        lowered = [s.lower() for s in sequential]
        if lowered[:4] == headers:
            sequential = sequential[4:]

        for i in range(0, len(sequential), 4):
            chunk = sequential[i : i + 4]
            if len(chunk) < 4:
                break
            serial, subcategory, description, price = [c.strip() for c in chunk]
            if serial.isdigit():
                rows.append(
                    {
                        "serial": serial,
                        "subcategory": subcategory,
                        "description": description,
                        "price": price,
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
