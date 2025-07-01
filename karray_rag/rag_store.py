import logging
from typing import List, Dict, Any, Optional
from haystack import Document
import json
from pathlib import Path
import re # Per il chunking

logger = logging.getLogger(__name__)

# --- 1. Gestione cache documenti JSONL ---
def save_documents_to_jsonl(documents: List[Document], path: str):
    """
    Salva una lista di oggetti Haystack Document in un file JSONL.
    Include il contenuto, i metadati e l'embedding (se presente).
    """
    try:
        # Assicurati che la directory esista
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for doc in documents:
                # Prepara il dizionario per la serializzazione
                doc_dict = {
                    "content": doc.content,
                    "meta": doc.meta if doc.meta is not None else {}, # Assicura che meta sia un dict
                    "embedding": getattr(doc, "embedding", None),
                }
                json.dump(doc_dict, f, ensure_ascii=False) # ensure_ascii=False per caratteri speciali
                f.write("\n")
        logger.info(f"✅ Salvati {len(documents)} documenti in {path}")
    except IOError as e:
        logger.error(f"❌ Errore I/O durante il salvataggio dei documenti in {path}: {e}")
    except Exception as e:
        logger.error(f"❌ Errore generico durante il salvataggio dei documenti: {e}")


def load_documents_from_jsonl(path: str) -> List[Document]:
    """
    Carica una lista di oggetti Haystack Document da un file JSONL.
    """
    documents = []
    file_path = Path(path)
    if not file_path.exists():
        logger.warning(f"⚠️ Il file {path} non esiste. Restituisco lista vuota.")
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    obj = json.loads(line)
                    # Assicurati che 'content' sia sempre una stringa e 'meta' un dict
                    content = str(obj.get("content", "")).strip()
                    meta = obj.get("meta", {})
                    embedding = obj.get("embedding")
                    
                    if not content:
                        logger.warning(f"⚠️ Linea {line_num}: Contenuto del documento vuoto. Saltato.")
                        continue

                    # Creazione del Documento Haystack
                    doc = Document(
                        content=content,
                        meta=meta,
                        embedding=embedding
                    )
                    documents.append(doc)
                except json.JSONDecodeError as jde:
                    logger.error(f"❌ Errore di decodifica JSON alla linea {line_num} in {path}: {jde}. Linea: '{line.strip()}'")
                except Exception as e:
                    logger.error(f"❌ Errore durante l'elaborazione del documento alla linea {line_num} in {path}: {e}. Linea: '{line.strip()}'")

        logger.info(f"✅ Caricati {len(documents)} documenti da {path}")
    except IOError as e:
        logger.error(f"❌ Errore I/O durante il caricamento dei documenti da {path}: {e}")
    except Exception as e:
        logger.error(f"❌ Errore generico durante il caricamento dei documenti: {e}")
    return documents

# --- 2. Funzioni di Chunking Avanzato ---
def chunk_document_by_sentences(document: Document, max_chars: int = 500, overlap_chars: int = 100) -> List[Document]:
    """
    Divide un documento in chunk basati su frasi, cercando di mantenere il contesto.
    Aggiunge un overlap tra i chunk per non perdere informazioni ai bordi.
    """
    chunks = []
    content = document.content
    
    # Suddividi il testo in frasi. Regex per individuare la fine delle frasi.
    sentences = re.split(r'(?<=[.!?])\s+', content)
    
    current_chunk_sentences = []
    current_chunk_length = 0
    
    for i, sentence in enumerate(sentences):
        # Prova ad aggiungere la frase corrente
        if current_chunk_length + len(sentence) + len(" ") <= max_chars:
            current_chunk_sentences.append(sentence)
            current_chunk_length += len(sentence) + len(" ")
        else:
            # Se la frase corrente non entra, crea un chunk dal buffer
            if current_chunk_sentences:
                chunk_content = " ".join(current_chunk_sentences).strip()
                if chunk_content:
                    chunks.append(Document(
                        content=chunk_content,
                        meta={**document.meta, "chunk_id": len(chunks), "original_source_doc_id": document.id}
                    ))
                
                # Prepara l'overlap per il prossimo chunk
                overlap_content = ""
                # Calcola quante frasi dell'overlap prendere dal fondo del chunk attuale
                temp_overlap_sentences = []
                temp_overlap_length = 0
                # Scorri le frasi del chunk attuale al contrario per trovare l'overlap
                for s_idx in range(len(current_chunk_sentences) -1, -1, -1):
                    s = current_chunk_sentences[s_idx]
                    if temp_overlap_length + len(s) + len(" ") <= overlap_chars:
                        temp_overlap_sentences.insert(0, s) # Inserisci all'inizio per mantenere l'ordine
                        temp_overlap_length += len(s) + len(" ")
                    else:
                        break
                overlap_content = " ".join(temp_overlap_sentences).strip()
                
                current_chunk_sentences = [s for s in temp_overlap_sentences] # Inizia il nuovo chunk con l'overlap
                current_chunk_length = len(overlap_content)
                
                # Aggiungi la frase corrente al nuovo chunk
                current_chunk_sentences.append(sentence)
                current_chunk_length += len(sentence) + len(" ")
            else:
                # Caso limite: la prima frase è già più grande di max_chars
                # O una singola frase è troppo lunga per entrare in un chunk vuoto
                # In questo caso, taglia la frase forzatamente (o gestisci diversamente)
                # Per semplicità, la aggiungiamo come un unico chunk tagliato se troppo grande
                logger.warning(f"⚠️ Frase troppo lunga per {max_chars} caratteri. Taglio forzato. Doc ID: {document.id}")
                chunk_content = sentence[:max_chars].strip()
                if chunk_content:
                    chunks.append(Document(
                        content=chunk_content,
                        meta={**document.meta, "chunk_id": len(chunks), "original_source_doc_id": document.id}
                    ))
                current_chunk_sentences = []
                current_chunk_length = 0

    # Aggiungi l'ultimo chunk rimanente
    if current_chunk_sentences:
        chunk_content = " ".join(current_chunk_sentences).strip()
        if chunk_content:
            chunks.append(Document(
                content=chunk_content,
                meta={**document.meta, "chunk_id": len(chunks), "original_source_doc_id": document.id}
            ))
            
    logger.debug(f"Documento originale di {len(content)} caratteri diviso in {len(chunks)} chunks.")
    return chunks

def chunk_documents(documents: List[Document], max_chars: int = 500, overlap_chars: int = 100) -> List[Document]:
    """
    Applica la strategia di chunking a una lista di documenti.
    """
    all_chunks = []
    for doc in documents:
        # Aggiungi un controllo di sicurezza per contenuti vuoti o molto corti
        if not doc.content or len(doc.content.strip()) < 50: # Minimo 50 caratteri per chunking
            logger.warning(f"⚠️ Documento saltato per chunking (contenuto troppo corto/vuoto): {doc.meta.get('source', 'N/A')}")
            if doc.content and len(doc.content.strip()) > 0: # Se non è vuoto, lo aggiungiamo come singolo "chunk"
                all_chunks.append(Document(
                    content=doc.content.strip(),
                    meta={**doc.meta, "chunk_id": 0, "original_source_doc_id": doc.id}
                ))
            continue
            
        chunks = chunk_document_by_sentences(doc, max_chars, overlap_chars)
        all_chunks.extend(chunks)
    logger.info(f"Splittati {len(documents)} documenti originali in {len(all_chunks)} chunks.")
    return all_chunks