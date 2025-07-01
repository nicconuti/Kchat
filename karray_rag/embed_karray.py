import logging
from pathlib import Path
import sys
from typing import List
import numpy as np
from haystack import Document
from haystack_integrations.components.embedders.ollama import OllamaDocumentEmbedder
from rag_store import load_documents_from_jsonl, save_documents_to_jsonl, chunk_documents
from sklearn.feature_extraction.text import TfidfVectorizer
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from models._call_llm import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INPUT_FILE = "data/karray_knowledge.jsonl"
OUTPUT_FILE = "data/embedded_karray_documents.jsonl"
MODEL_NAME = "mxbai-embed-large"
CHUNK_MAX_CHARS = 500
CHUNK_OVERLAP_CHARS = 100

def deduplicate_by_content(docs: List[Document]) -> List[Document]:
    seen_hashes = set()
    temp_docs_map = {}
    for doc in docs:
        if not doc.content:
            logger.warning(f"⚠️ Documento vuoto: {doc.meta}")
            continue
        h = hash(doc.content.strip())
        if h not in seen_hashes:
            seen_hashes.add(h)
            temp_docs_map[h] = doc
    return list(temp_docs_map.values())

def extract_keywords_tfidf(text: str, top_k: int = 5) -> List[str]:
    vectorizer = TfidfVectorizer(stop_words="english", max_features=top_k)
    try:
        X = vectorizer.fit_transform([text])
        return vectorizer.get_feature_names_out().tolist()
    except Exception as e:
        logger.warning(f"❌ Errore estrazione keyword: {e}")
        return []

def validate_keywords_with_llm(text: str, raw_keywords: List[str], llm_client: LLMClient) -> List[str]:
    prompt = (
        "Given the following document:\n"
        f"{text[:800]}\n\n"
        f"These are the auto-extracted keywords: {raw_keywords}.\n"
        "Now return the 3 to 5 most semantically relevant keywords from that list as a JSON array of strings.\n"
        "The format must be: [\"keyword1\", \"keyword2\", \"keyword3\"]"
    )

    try:
        result = LLMClient.call_json(llm_client,prompt)
        if result and isinstance(result, list):
            # Verifica che siano effettivamente tutte stringhe
            return [kw for kw in result if isinstance(kw, str)]
        else:
            logger.warning(f"⚠️ LLM ha restituito un risultato inatteso: {result}")
            return []
    except Exception as e:
        logger.warning(f"⚠️ Errore nella validazione semantica via LLM: {e}")
        return []

def is_valid_embedding(embedding) -> bool:
    if isinstance(embedding, list):
        return not any(isinstance(x, (float, int)) and x != x for x in embedding)
    elif isinstance(embedding, np.ndarray):
        return not np.isnan(embedding).any()
    return False

def main():
    logger.info("📥 Caricamento documenti...")
    documents = load_documents_from_jsonl(INPUT_FILE)
    if not documents:
        logger.error("❌ Nessun documento trovato.")
        return

    documents = deduplicate_by_content(documents)
    logger.info(f"📄 Documenti deduplicati: {len(documents)}")

    logger.info("✂️ Suddivisione in chunks...")
    chunks = chunk_documents(documents, max_chars=CHUNK_MAX_CHARS, overlap_chars=CHUNK_OVERLAP_CHARS)
    if not chunks:
        logger.error("❌ Nessun chunk generato.")
        return
    logger.info(f"📄 Chunks da embeddare: {len(chunks)}")

    logger.info(f"🧠 Inizializzazione embedder `{MODEL_NAME}`...")
    embedder = OllamaDocumentEmbedder(model=MODEL_NAME, url="http://localhost:11434")

    try:
        logger.info("🚀 Embedding in corso...")
        result = embedder.run(documents=chunks)
        embedded_documents = result["documents"]

        clean_embedded_documents = []
        llm_client = LLMClient(default_model="deepseek-r1:8b") 

        for doc in embedded_documents:
            if not hasattr(doc, 'embedding') or not is_valid_embedding(doc.embedding):
                logger.warning(f"⚠️ Embedding non valido. Source: {doc.meta.get('source', 'N/A')}")
                continue

            # --- Keyword extraction and LLM validation ---
            keywords = extract_keywords_tfidf(doc.content)
            validated = validate_keywords_with_llm(doc.content, keywords, llm_client)
            doc.meta["categories"] = keywords
            doc.meta["validated_categories"] = validated

            clean_embedded_documents.append(doc)

        if not clean_embedded_documents:
            logger.error("❌ Nessun documento valido post-embedding.")
            return

        logger.info(f"✅ Documenti embedded e arricchiti: {len(clean_embedded_documents)}")
        save_documents_to_jsonl(clean_embedded_documents, OUTPUT_FILE)
        logger.info(f"📁 Salvati in: {OUTPUT_FILE}")

    except Exception as e:
        logger.error(f"❌ Errore embedding: {e}")
        logger.info("Verifica se Ollama è attivo e il modello corretto avviato.")
        return

if __name__ == "__main__":
    main()
