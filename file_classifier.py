from __future__ import annotations

import argparse
import json
from pathlib import Path

from categorizer import Categorizer


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
    args = parser.parse_args()
    cat = Categorizer(mode=args.mode)
    data = cat.run(Path(args.input_path))
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
