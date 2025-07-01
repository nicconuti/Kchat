"""Background agent to ingest and embed documents with real embeddings."""

import json
import numpy as np
from pathlib import Path
from typing import Any, List, Mapping, Dict, Optional, Union
from dataclasses import dataclass

from agents.context import AgentContext
from utils.logger import get_logger

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = get_logger("ingest_log")

# Global model instance for efficiency
_embedding_model: Optional[SentenceTransformer] = None
_qdrant_client: Optional[QdrantClient] = None

# Configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Lightweight, multilingual model
COLLECTION_NAME = "documents"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


@dataclass
class DocumentChunk:
    """Represents a document chunk with its embedding."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


def get_embedding_model() -> Optional[SentenceTransformer]:
    """Get or initialize the embedding model."""
    global _embedding_model
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        logger.error("sentence-transformers not available")
        return None
    
    if _embedding_model is None:
        try:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    
    return _embedding_model


def get_qdrant_client() -> Optional[QdrantClient]:
    """Get or initialize the Qdrant client."""
    global _qdrant_client
    
    if not QDRANT_AVAILABLE:
        logger.warning("qdrant-client not available, using local file storage")
        return None
    
    if _qdrant_client is None:
        try:
            # Try to connect to local Qdrant instance
            _qdrant_client = QdrantClient(host="localhost", port=6333)
            
            # Create collection if it doesn't exist
            try:
                _qdrant_client.get_collection(COLLECTION_NAME)
            except Exception:
                # Collection doesn't exist, create it
                logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
                _qdrant_client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)  # MiniLM-L6 embedding size
                )
                logger.info("Qdrant collection created successfully")
                
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}, falling back to file storage")
            _qdrant_client = None
    
    return _qdrant_client


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Chunk text into overlapping segments."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at word boundaries
        if end < len(text):
            # Look for the last space before the end
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def create_embeddings(texts: List[str]) -> List[List[float]]:
    """Create embeddings for a list of texts."""
    model = get_embedding_model()
    if model is None:
        # Fallback to simple hash-based embeddings
        logger.warning("Using fallback hash-based embeddings")
        return [[float(hash(text + str(i)) % 1000) / 1000.0 for i in range(384)] for text in texts]
    
    try:
        embeddings = model.encode(texts, convert_to_tensor=False, normalize_embeddings=True)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Error creating embeddings: {e}")
        # Fallback to hash-based embeddings
        return [[float(hash(text + str(i)) % 1000) / 1000.0 for i in range(384)] for text in texts]


def store_in_qdrant(chunks: List[DocumentChunk]) -> bool:
    """Store document chunks in Qdrant vector database."""
    client = get_qdrant_client()
    if client is None:
        return False
    
    try:
        points = []
        for chunk in chunks:
            if chunk.embedding:
                point = PointStruct(
                    id=hash(chunk.id),  # Use hash of ID as point ID
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "chunk_id": chunk.id
                    }
                )
                points.append(point)
        
        if points:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            logger.info(f"Stored {len(points)} chunks in Qdrant")
            return True
        
    except Exception as e:
        logger.error(f"Error storing in Qdrant: {e}")
    
    return False


def store_in_file(chunks: List[DocumentChunk], filepath: Path) -> bool:
    """Store document chunks in local JSON file as fallback."""
    try:
        # Load existing data
        data = {}
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Add new chunks
        for chunk in chunks:
            data[chunk.id] = {
                "content": chunk.content,
                "metadata": chunk.metadata,
                "embedding": chunk.embedding
            }
        
        # Save updated data
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Stored {len(chunks)} chunks in file: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing in file: {e}")
        return False


def extract_text_from_file(path: Path) -> str:
    """Extract text from various file formats."""
    try:
        if path.suffix.lower() == '.txt':
            return path.read_text(encoding='utf-8')
        elif path.suffix.lower() == '.json':
            # Handle JSON files (like product catalogs)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            # For other formats, try to read as text
            return path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error extracting text from {path}: {e}")
        return ""


def run(context: AgentContext, path: Union[str, Path], metadata: Optional[Mapping[str, Any]] = None) -> AgentContext:
    """Ingest and embed documents with real embeddings."""
    path = Path(path)
    
    try:
        # Extract text from file
        if not path.exists():
            logger.error(f"File not found: {path}")
            context.error_flag = True
            context.source_reliability = 0.0
            return context
        
        text = extract_text_from_file(path)
        if not text:
            logger.warning(f"No text extracted from {path}")
            context.source_reliability = 0.1
            return context
        
        # Create chunks
        text_chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        logger.info(f"Created {len(text_chunks)} chunks from {path.name}")
        
        # Create embeddings
        embeddings = create_embeddings(text_chunks)
        
        # Create document chunks
        chunks = []
        base_metadata = {
            "source_file": str(path),
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "chunk_count": len(text_chunks),
            **(metadata or {})
        }
        
        for i, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings)):
            chunk_id = f"{path.stem}_{i:04d}"
            chunk_metadata = {
                **base_metadata,
                "chunk_index": i,
                "chunk_id": chunk_id
            }
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                metadata=chunk_metadata,
                embedding=embedding
            )
            chunks.append(chunk)
        
        # Store chunks
        storage_success = False
        
        # Try Qdrant first
        if store_in_qdrant(chunks):
            storage_success = True
            logger.info("Documents stored in Qdrant successfully")
        else:
            # Fallback to file storage
            storage_file = Path("embeddings") / f"{path.stem}_embeddings.json"
            if store_in_file(chunks, storage_file):
                storage_success = True
                logger.info("Documents stored in file successfully")
        
        # Update context
        if storage_success:
            context.documents = [chunk.id for chunk in chunks]
            context.source_reliability = 0.95
            
            # Store some metadata for potential use by other agents
            if metadata:
                context.reasoning_trace = str(metadata.get("entities", []))
        else:
            context.error_flag = True
            context.source_reliability = 0.2
            logger.error("Failed to store document chunks")
        
        logger.info(
            f"ingested {len(chunks)} chunks from {path.name}",
            extra={
                "confidence_score": context.confidence,
                "source_reliability": context.source_reliability,
                "clarification_attempted": context.clarification_attempted,
                "error_flag": context.error_flag,
                "chunks_created": len(chunks),
                "embedding_model": EMBEDDING_MODEL_NAME if SENTENCE_TRANSFORMERS_AVAILABLE else "hash_fallback",
                "storage_backend": "qdrant" if get_qdrant_client() else "file"
            },
        )
        
    except Exception as e:
        logger.error(f"Error during document ingestion: {e}", exc_info=True)
        context.error_flag = True
        context.source_reliability = 0.0
    
    return context
