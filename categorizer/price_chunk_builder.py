from __future__ import annotations

import os
import re
import json
import pandas as pd
from decimal import Decimal, InvalidOperation
from typing import List, Dict
from models.call_local_llm import call_mistral
from utils.logger import get_json_logger

logger = get_json_logger("mistral_price_parser")


def get_enhanced_preview(df: pd.DataFrame) -> List[List[str]]:
    total_rows = len(df)
    if total_rows < 60:
        return df.fillna("").astype(str).values.tolist()
    else:
        first = df.iloc[:20].fillna("").astype(str).values.tolist()
        middle = df.iloc[total_rows // 2: total_rows // 2 + 20].fillna("").astype(str).values.tolist()
        last = df.iloc[-20:].fillna("").astype(str).values.tolist()
        return first + middle + last


def generate_sheet_analysis_prompt(previews: dict[str, list[list[str]]]) -> str:
    prompt = (
        "You are a spreadsheet analyst.\n"
        "Your task is to analyze the structure of multiple Excel sheets from a pricing document.\n"
        "Each sheet may contain different layouts, headers, subcategories, and product records.\n"
        "For each sheet, output a JSON object like:\n"
        "{\n"
        "  \"INSTALLED\": {\n"
        "    \"contains_prices\": true,\n"
        "    \"has_subcategories\": true,\n"
        "    \"subcategory_hint\": \"single non-empty cell rows\",\n"
        "    \"expected_fields\": [\"serial\", \"description\", \"price\"],\n"
        "    \"comments\": \"Header appears around row 5; data starts after subcategory rows\"\n"
        "  }, ...\n"
        "}\n\n"
        "Now analyze the following sheet previews:\n"
    )
    for sheet_name, rows in previews.items():
        preview_text = "\n".join(" | ".join(row) for row in rows if any(cell.strip() for cell in row))
        prompt += f"\n---\nSheet: {sheet_name}\n{preview_text}\n"
    prompt += "\n\n### JSON output:\n"
    return prompt


def parse_sheet_rows_with_mistral(sheet_name: str, df: pd.DataFrame) -> List[Dict[str, str]]:
    df = df.fillna("").astype(str)
    rows = df.values.tolist()
    preview_text = "\n".join(" | ".join(row) for row in rows if any(cell.strip() for cell in row))

    prompt = f"""
You are an expert in transforming Excel tables into structured JSON price lists.

The following is a sheet named '{sheet_name}' from a pricing Excel document.
Each block may contain a subcategory name followed by rows with serials, prices, and descriptions.

Extract every valid data row as a JSON object with:
- serial (e.g., 'GSP-MCA057B98MON')
- description (human-readable name)
- price (in euros, like 123.00)
- subcategory (a list like ['INSTALL', 'KAN200'])

Skip irrelevant rows or headers.

Output format: JSON array of structured objects.

Strict rules:
- Do not include comments like // or explanations
- Do not use trailing commas
- Do not wrap JSON in any object (just an array)


---
{preview_text}

JSON:
""".strip()

    try:
        logger.debug(f"[{sheet_name}] Mistral prompt:\n{prompt[:1000]}...")
        raw = call_mistral(prompt)
        logger.debug(f"[{sheet_name}] Mistral raw response:\n{raw[:2000]}...")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"[{sheet_name}] Invalid JSON output from Mistral: {e}\nRaw:\n{raw[:1000]}")
            return []

        if isinstance(data, list):
            logger.info(f"[{sheet_name}] Parsed {len(data)} rows successfully from Mistral output.")
            return data
        else:
            raise ValueError("Mistral output was not a JSON list.")
    except Exception as e:
        logger.warning(f"[{sheet_name}] Failed to parse Mistral output: {e}")
        return []


def parse_price_table(xls: pd.ExcelFile) -> List[Dict[str, str]]:
    records = []
    for sheet in xls.sheet_names:
        try:
            logger.info(f"Processing sheet: {sheet}")
            df = xls.parse(sheet)
            sheet_records = parse_sheet_rows_with_mistral(sheet, df)
            records.extend(sheet_records)
        except Exception as e:
            logger.error(f"Error processing sheet '{sheet}': {e}")
    return records


def safe_price_parse(val: str) -> str | None:
    val = re.sub(r"[^\d,\.]", "", val)
    if val.count(",") == 1 and val.count(".") == 0:
        val = val.replace(",", ".")
    try:
        return f"{float(Decimal(val)):.2f}"
    except (ValueError, InvalidOperation):
        return None


def normalize_prices(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    cleaned = []
    for record in records:
        try:
            price = record.get("price", "")
            normalized = safe_price_parse(price)
            if normalized:
                record["price"] = normalized
                cleaned.append(record)
            else:
                logger.debug(f"Ignored invalid price: {price}")
        except Exception as e:
            logger.warning(f"Error normalizing price: {e}")
    logger.info(f"Normalized {len(cleaned)} valid price rows.")
    return cleaned


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python mistral_price_parser.py <path_to_excel_file>")
        exit(1)

    xls_path = sys.argv[1]
    xls = pd.ExcelFile(xls_path)

    raw_records = parse_price_table(xls)
    normalized_records = normalize_prices(raw_records)

    print(json.dumps(normalized_records, indent=2, ensure_ascii=False))
