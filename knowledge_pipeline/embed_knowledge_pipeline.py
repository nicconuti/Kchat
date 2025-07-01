import logging
from pathlib import Path
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.preprocessors import DocumentSplitter
from haystack.dataclasses import Document
from karray_rag.rag_store import load_documents_from_jsonl, save_documents_to_jsonl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmbedKnowledge")

INPUT_FILE = Path("data/knowledge_base_reliable.jsonl")
OUTPUT_FILE = Path("data/embedded_knowledge_docs.jsonl")


def main():
    if not INPUT_FILE.exists():
        logger.error(f"File non trovato: {INPUT_FILE}")
        return

    # Carica i documenti chunkati e arricchiti
    documents = load_documents_from_jsonl(INPUT_FILE)
    logger.info(f"Chunk caricati: {len(documents)}")

    # Chunking (eventuale rifragmentazione)
    splitter = DocumentSplitter(
        split_by="word",
        split_length=300,
        split_overlap=30,
        respect_sentence_boundary=True,
    )
    split_docs = splitter.run(documents=documents)["documents"]
    logger.info(f"Documenti dopo splitting: {len(split_docs)}")

    # Embedding con MiniLM
    embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
    embedded_docs = embedder.run(documents=split_docs)["documents"]

    # Salvataggio
    save_documents_to_jsonl(embedded_docs, str(OUTPUT_FILE))
    logger.info(f"✅ Embedding completato. Salvato in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
