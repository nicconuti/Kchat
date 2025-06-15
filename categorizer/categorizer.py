from __future__ import annotations

from pathlib import Path
from datetime import datetime

from .scanner import scan
from .extractor import extract_text
from .classifier import classify
from .chunk_builders import build_chunks
from .entity_extractor import extract_entities
from .validator import confirm

from utils.logger import get_json_logger

logger = get_json_logger("categorizer_log")


class Categorizer:
    def __init__(self, mode: str = "interactive", threshold: float = 0.9, main_category: str | None = None) -> None:
        self.mode = mode
        self.threshold = threshold
        self.main_category = main_category

    def process_file(self, path: Path) -> dict:
        text = extract_text(path)
        category, subcats, conf, ambiguous = classify(text, path.name)
        if self.main_category:
            category = self.main_category
            validated = True
            source = "forced"
        else:
            category, subcats, validated, source, conf = confirm(
                category,
                subcats,
                text,
                path.name,
                mode=self.mode,
                confidence=conf,
            )
        entities = extract_entities(text)
        metadata = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "file_size_kb": path.stat().st_size // 1024,
            "word_count": len(text.split()),
            "processed_at": datetime.utcnow().isoformat(),
            "entities": entities,
        }
        chunks = build_chunks(text, category) if category else []
        logger.info(
            "processed",
            extra={
                "file": str(path),
                "category": category,
                "confidence_score": conf,
                "clarification_attempted": ambiguous,
            },
        )
        return {
            "file": str(path),
            "category": category,
            "subcategories": subcats,
            "validated": validated,
            "metadata": metadata,
            "category_source": source,
            "confidence": conf,
            "chunks": chunks,
        }

    def run(self, root: Path) -> list[dict]:
        files, tmp = scan(root)
        results = [self.process_file(f) for f in files if f.exists()]
        if tmp:
            tmp.cleanup()
        return [r for r in results if r["category"]]
