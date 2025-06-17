from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from models.call_local_llm import call_mistral


def load_csv(path: str | Path) -> list[dict[str, Any]]:
    """Load ``path`` into a list of rows using pandas.

    If parsing with default settings fails, retry without header and
    assign generic column names.
    """
    p = Path(path)
    try:
        df = pd.read_csv(p)
        if all(str(c).isdigit() for c in df.columns):
            raise ValueError("numeric_header")
    except Exception:
        df = pd.read_csv(p, header=None)
        df.columns = [f"col_{i}" for i in range(len(df.columns))]  # type: ignore[assignment]
    return df.fillna("").to_dict(orient="records")  # type: ignore[return-value]


def summarize_csv(path: str | Path, sample_rows: int = 3) -> str:
    """Return a short summary of the CSV structure using Mistral."""
    p = Path(path)
    df = pd.read_csv(p, nrows=sample_rows)
    rows = df.fillna("").to_dict(orient="records")
    prompt = (
        "Describe the meaning of the columns in this CSV in one sentence.\n"
        f"Rows: {rows}\nSummary:"
    )
    try:
        return call_mistral(prompt).strip()
    except Exception:
        return ""
