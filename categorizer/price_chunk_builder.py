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

    rows = []
    current_subcategory = None

    df = df.fillna("").astype(str)

    for _, row in df.iterrows():
        serial = row.get(serial_col, "").strip()
        description = row.get(description_col, "").strip()
        price_raw = row.get(price_col, "").strip()

        if not serial and not price_raw and not description:
            continue

        # Heuristic per subcategoria (solo se è una sigla tecnica senza price/desc)
        if serial and not price_raw and not description and re.match(r"^[A-Z]{2,}\d{2,}[A-Z]?$", serial):
            current_subcategory = serial
            continue

        price = re.sub(r"[^\d,\.]", "", price_raw).replace(",", ".")
        if not re.match(r"^\d+(\.\d+)?$", price):
            continue

        rows.append({
            "serial": serial,
            "subcategory": [current_subcategory] if current_subcategory else [],
            "description": description,
            "price": price,
        })

    return rows


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
    }

    is_subcategory = is_subcategory or (lambda line: re.match(r"^[A-Z]{2,}\d{2,}[A-Z]?$", line))

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    subcat_map = {idx: line for idx, line in enumerate(lines) if is_subcategory(line)}

    header_row = []
    header_index = -1

    for i, line in enumerate(lines):
        if any(alias.lower() in line.lower() for aliases in field_aliases.values() for alias in aliases):
            header_row = re.split(r"\t+| {2,}", line)
            header_index = i
            break

    if not header_row:
        raise ValueError("Impossibile trovare l’intestazione della tabella.")

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

    current_sub = None
    output = []

    for i, line in enumerate(lines[header_index + 1:], start=header_index + 1):
        if i in subcat_map:
            current_sub = subcat_map[i]
            continue

        parts = re.split(r"\t+| {2,}", line)
        if len(parts) < len(column_map):
            continue

        try:
            serial = parts[column_map["serial"]].strip()
            description = parts[column_map["description"]].strip()
            price_raw = parts[column_map["price"]].strip()
            price = re.sub(r"[^\d,\.]", "", price_raw).replace(",", ".")

            if not re.match(r"^\d+(\.\d+)?$", price):
                continue

            output.append({
                "serial": serial,
                "subcategory": [current_sub] if current_sub else [] + ([parent_category] if parent_category else []),
                "description": description,
                "price": price,
            })
        except Exception:
            continue

    return output
