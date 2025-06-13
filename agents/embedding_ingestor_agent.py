"""Background agent to ingest and embed documents."""

from pathlib import Path

from agents.context import AgentContext
from utils.logger import get_logger


logger = get_logger("ingest_log")


def run(context: AgentContext, path: str | Path) -> AgentContext:
    path = Path(path)
    if path.exists():
        text = path.read_text()
    else:
        text = "dummy"
    chunks = [text[i:i+10] for i in range(0, len(text), 10)]
    embeddings = [hash(c) % 1000 for c in chunks]
    context.documents = [f"{path.name}-{i}" for i, _ in enumerate(embeddings)]
    context.source_reliability = 1.0
    logger.info(
        f"ingested {len(chunks)} chunks from {path.name}",
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
