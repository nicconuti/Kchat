from __future__ import annotations

import argparse
import json
from pathlib import Path

from categorizer import Categorizer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

VALID_CATEGORIES = [
    "tech_assistance",
    "software_assistance",
    "product_price",
    "product_guide",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify files in a folder or zip")
    parser.add_argument("input_path")
    parser.add_argument("--output", default="output.json")
    parser.add_argument(
        "--mode",
        choices=["interactive", "auto", "silent"],
        default="interactive",
        help="Confirmation mode",
    )
    parser.add_argument(
        "--category",
        required=True,
        choices=VALID_CATEGORIES,
        help="Forced main category",
    )
    args = parser.parse_args()
    cat = Categorizer(mode=args.mode, main_category=args.category)
    data = cat.run(Path(args.input_path))

    output_path = Path(args.output)
    if args.category == "product_price":
        output_path = Path("prices.json")
        try:
            existing = json.loads(output_path.read_text())
            if not isinstance(existing, list):
                existing = []
        except FileNotFoundError:
            existing = []
        except json.JSONDecodeError:
            existing = []
        existing.extend(data)
        output_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    else:
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


app = FastAPI()


class ClassifyRequest(BaseModel):
    input_path: str
    category: str
    mode: str = "interactive"


@app.post("/classify")
def classify_endpoint(req: ClassifyRequest) -> List[dict]:
    if req.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    cat = Categorizer(mode=req.mode, main_category=req.category)
    data = cat.run(Path(req.input_path))
    return data


if __name__ == "__main__":
    main()
