"""Retrieve relevant document chunks using a local Qdrant instance."""

from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from agents.context import AgentContext
from utils.logger import get_logger


DOCS = {
    "manual": [
        {"content": "manual section 1", "roles": ["user", "admin"]},
        {"content": "manual section 2", "roles": ["user", "admin"]},
    ],
    "setup": [
        {"content": "setup guide", "roles": ["admin"]},
    ],
}


def _embed(text: str) -> List[float]:
    """Generate a simple deterministic embedding vector."""
    h = abs(hash(text))
    return [
        ((h >> 0) & 0xFF) / 255,
        ((h >> 8) & 0xFF) / 255,
        ((h >> 16) & 0xFF) / 255,
    ]


_client = QdrantClient(":memory:")
_COLLECTION = "docs"
_client.recreate_collection(
    collection_name=_COLLECTION,
    vectors_config=rest.VectorParams(size=3, distance=rest.Distance.COSINE),
)
_points: List[rest.PointStruct] = []
idx = 1
for docs in DOCS.values():
    for d in docs:
        _points.append(
            rest.PointStruct(
                id=idx,
                vector=_embed(str(d["content"])),
                payload={"content": d["content"], "roles": d["roles"]},
            )
        )
        idx += 1
_client.upsert(collection_name=_COLLECTION, points=_points)


def _retrieve(query: str, role: str) -> List[str]:
    qvec = _embed(query)
    results = _client.search(
        collection_name=_COLLECTION, query_vector=qvec, limit=5
    )
    allowed = []
    for res in results:
        payload = res.payload or {}
        content = payload.get("content", "")
        if role in payload.get("roles", []) and query.lower() in content.lower():
            allowed.append(content)
    return allowed


logger = get_logger("retrieval_log")


def run(context: AgentContext, query: Optional[str] = None) -> AgentContext:
    if context.role == "guest":
        context.error_flag = True
        logger.info(
            "permission denied",
            extra={
                "confidence_score": context.confidence,
                "source_reliability": context.source_reliability,
                "clarification_attempted": context.clarification_attempted,
                "error_flag": context.error_flag,
            },
        )
        return context

    docs = _retrieve(query or context.input, context.role)
    context.documents = docs
    context.source_reliability = 0.9 if docs else 0.5
    logger.info(
        f"retrieved {len(context.documents)} docs",
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
