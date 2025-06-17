from __future__ import annotations
import re
import difflib
import json
import pandas as pd
from typing import List, Dict, Callable
from models.mistral import call_mistral


def infer_column_mapping_with_llm(df: pd.DataFrame, model: str = "mistral") -> Dict[str, str]:
    header = list(df.columns)
    sample = df.head(6).fillna("").values.tolist()

    prompt = f"""
You are an expert at analyzing spreadsheet structures.

Based on the header and data sample below, identify which columns correspond to the following fields:
- serial number (a unique part number like SKU or ID)
- description (human-readable name or explanation of the part)
- price (a monetary value in euro or any currency)

Output your answer strictly as a JSON object with keys: serial, description, price.
Do not explain anything. Do not add comments or formatting.

Header:
{json.dumps(header)}

Sample rows:
{json.dumps(sample)}

JSON:
"""
    raw = call_mistral(prompt, model=model)
    try:
        result = json.loads(raw)
        if all(k in result for k in ("serial", "description", "price")):
            return result
        else:
            raise ValueError("Missing expected keys in LLM output.")
    except Exception as e:
        raise ValueError(f"Failed to parse LLM output: {e}")


def parse_price_table_from_excel(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Estrae righe strutturate da un DataFrame Excel,
    inferendo le colonne tramite LLM locale (no hardcoded mapping).
    """
    column_map = infer_column_mapping_with_llm(df)

    serial_col = column_map["serial"]
    description_col = column_map["description"]
    price_col = column_map["price"]

    df = df.fillna("").astype(str)

    lines = ["serial\tdescription\tprice"]
    for _, row in df.iterrows():
        serial = row.get(serial_col, "").strip()
        description = row.get(description_col, "").strip()
        price = row.get(price_col, "").strip()

        if not serial and not price and not description:
            continue

        if serial and not price and not description:
            lines.append(serial)
        else:
            lines.append(f"{serial}\t{description}\t{price}")

    text = "\n".join(lines)
    return parse_price_table(text)


def parse_price_table(
    text: str,
    field_aliases: Dict[str, List[str]] | None = None,
    is_subcategory: Callable[[str], bool] | None = None,
    parent_category: str | None = None,
) -> List[Dict[str, str]]:
    """
    Parsing destrutturato da testo. Permette:
    - alias colonne (fallback heuristico)
    - regex subcategorie
    - definizione dinamica del contesto
    """
    field_aliases = field_aliases or {
        "serial": ["serial", "sku", "id", "code"],
        "price": ["price", "prezzo", "importo", "€", "cost"],
        "description": ["description", "descrizione", "name", "product"],
        "subcategory": ["subcategory", "category", "group"],
    }

    if is_subcategory is None:
        def is_subcategory(line: str) -> bool:
            return bool(re.match(r"^[A-Z]{2,}\d{2,}[A-Z]?$", line))

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    subcat_map = {idx: line for idx, line in enumerate(lines) if is_subcategory(line)}

    header_row = []
    header_index = -1

    for i, line in enumerate(lines):
        parts = re.split(r"\s*\|\s*|\t+| {2,}", line)
        alias_hits = sum(
            1
            for p in parts
            for aliases in field_aliases.values()
            for alias in aliases
            if p.lower() == alias.lower()
        )
        if alias_hits >= 2:
            header_row = parts
            header_index = i
            break

    if not header_row:
        potential = lines[:len(field_aliases)]
        aliases = [a.lower() for aliases in field_aliases.values() for a in aliases]
        if all(p.lower() in aliases for p in potential):
            header_row = potential
            header_index = 0
            body = lines[len(header_row):]
            new_lines = [" | ".join(header_row)]
            step = len(header_row)
            for j in range(0, len(body), step):
                row = body[j:j + step]
                if len(row) == step:
                    new_lines.append(" | ".join(row))
            lines = new_lines
        else:
            return []

    def detect_columns(header_row: List[str], field_aliases: Dict[str, List[str]]) -> Dict[str, int]:
        resolved = {}
        for logical_name, aliases in field_aliases.items():
            for alias in aliases:
                match = difflib.get_close_matches(alias.lower(), [h.lower() for h in header_row], n=1, cutoff=0.6)
                if match:
                    index = [h.lower() for h in header_row].index(match[0])
                    resolved[logical_name] = index
                    break
        return resolved

    column_map = detect_columns(header_row, field_aliases)
    required = {"serial", "price", "description"}
    if not required.issubset(column_map):
        raise ValueError(f"Colonne richieste non trovate: {required - set(column_map)}")
    sub_idx = column_map.get("subcategory")

    current_sub = None
    output = []

    for i, line in enumerate(lines[header_index + 1:], start=header_index + 1):
        if i in subcat_map:
            current_sub = subcat_map[i]
            continue

        parts = re.split(r"\s*\|\s*|\t+| {2,}", line)
        if len(parts) < len(column_map):
            continue

        try:
            serial = parts[column_map["serial"]].strip()
            description = parts[column_map["description"]].strip()
            price_raw = parts[column_map["price"]].strip()
            price = re.sub(r"[^\d,\.]", "", price_raw).replace(",", ".")

            if not re.match(r"^\d+(\.\d+)?$", price):
                continue

            sub_value = parts[sub_idx].strip() if sub_idx is not None else current_sub
            subs = []
            if sub_value:
                subs.append(sub_value)
            elif current_sub:
                subs.append(current_sub)
            if parent_category:
                subs.append(parent_category)
            output.append({
                "serial": serial,
                "subcategory": ", ".join(subs) if subs else "",
                "description": description,
                "price": price,
            })
        except Exception:
            continue

    return output
