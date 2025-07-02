import argparse
import concurrent.futures
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from karray_rag.rag_store import save_documents_to_jsonl

from .config import PipelineConfig
from .logging_config import setup_logging
from .components import FileScanner, TextExtractor, EntityExtractor
from .chunking import AdvancedSemanticChunker, ChunkingStrategy, StructuredDataExtractor
from .llm_utils import (
    call_llm_for_classification,
    call_llm_for_enrichment,
    fallback_llm_client,
    primary_llm_client,
)

logger = setup_logging()


class KnowledgePipeline:
    """Orchestra il processo di ingestione con focus su affidabilità e parallelismo."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.scanner = FileScanner(config.SUPPORTED_EXTENSIONS)
        self.text_extractor = TextExtractor()
        self.entity_extractor = EntityExtractor()
        self.chunker_map: Dict[str, ChunkingStrategy] = {
            "product_price": StructuredDataExtractor(),
            "default": AdvancedSemanticChunker(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP,
            ),
        }
        for cat in config.SEMANTIC_CATEGORIES:
            if cat not in self.chunker_map:
                self.chunker_map[cat] = self.chunker_map["default"]
        self.quarantine_path = Path(config.QUARANTINE_DIR)
        self.quarantine_path.mkdir(exist_ok=True)

    def _quarantine_file(self, file_path: Path, reason: str) -> None:
        try:
            self.quarantine_path.mkdir(parents=True, exist_ok=True)
            quarantine_target = self.quarantine_path / f"{pd.Timestamp.utcnow().strftime('%Y%m%d%H%M%S')}_{file_path.name}"
            logger.warning(f"Metto in quarantena il file '{file_path.name}'. Motivo: {reason}")
            shutil.copy(str(file_path), str(quarantine_target))
            with open(self.quarantine_path / f"{quarantine_target.name}.reason.log", "w", encoding="utf-8") as f:
                f.write(
                    f"File in quarantena a {pd.Timestamp.utcnow().isoformat()}\nMotivo: {reason}\nPercorso originale: {file_path}\n"
                )   
            try:
                snapshot_text = file_path.read_text(encoding="utf-8", errors="ignore")
                with open(self.quarantine_path / f"{quarantine_target.name}.txt", "w", encoding="utf-8") as snap:
                    snap.write(snapshot_text[:100000])
            except Exception as e:  # pragma: no cover - log warning
                logger.warning(f"Impossibile salvare snapshot per {file_path.name}: {e}")
        except Exception:  # pragma: no cover - log critical
            logger.critical(
                f"Impossibile mettere in quarantena il file {file_path.name}. Richiede intervento manuale.",
                exc_info=True,
            )

    def process_file(self, path: Path) -> List[Dict[str, Any]]:
        logger.info(f"Avvio elaborazione per il file: {path.name}")
        document_id = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
        raw_text = self.text_extractor.extract(
            path,
            self.config.MIN_EXTRACTED_TEXT_SIZE,
            self.config.TABLE_PREVIEW_ROWS,
        )
        if not raw_text:
            self._quarantine_file(path, "Estrazione del testo fallita o contenuto del file vuoto dopo lo strip.")
            return []

        text_for_classification = raw_text[: self.config.FULL_TEXT_CLASSIFICATION_LIMIT]
        llm_response = call_llm_for_classification(
            text_for_classification,
            path.name,
            self.config.SEMANTIC_CATEGORIES,
            "deepseek-r1:14b",
            client=primary_llm_client,
        )
        category = llm_response.get("category", "unclassified")
        confidence = llm_response.get("confidence", 0.0)

        review_reason = None
        if not category or category == "unclassified":
            review_reason = (
                f"LLM non è riuscito a classificare o ha restituito 'unclassified'. Confidenza: {confidence:.2f}"
            )
            self._quarantine_file(path, review_reason)
            return []

        logger.info(f"Classificazione iniziale per '{path.name}': {category} (Confidenza: {confidence:.2f})")

        if confidence < self.config.CROSS_CHECK_CONFIDENCE_THRESHOLD:
            logger.info(
                f"Confidenza per '{path.name}' inferiore alla soglia ({confidence:.2f} < {self.config.CROSS_CHECK_CONFIDENCE_THRESHOLD}). Eseguo cross-check..."
            )
            cross_check_response = call_llm_for_classification(
                text_for_classification,
                path.name,
                self.config.SEMANTIC_CATEGORIES,
                "mistral",
                client=fallback_llm_client,
            )
            cross_check_category = cross_check_response.get("category")
            if not cross_check_category or cross_check_category != category:
                review_reason = (
                    f"Discrepanza di classificazione. Primaria ({primary_llm_client.default_model}): {category} (Conf: {confidence:.2f}), "
                    f"Secondaria ({fallback_llm_client.default_model}): {cross_check_category} (Conf: {cross_check_response.get('confidence',0.0):.2f})."
                )
                self._quarantine_file(path, review_reason)
                return []
            else:
                logger.info(
                    f"Cross-check per '{path.name}' completato con successo. Modelli primario e secondario concordano."
                )

        entities = self.entity_extractor.extract(raw_text)
        product_status = "active"
        if category == "product_price" and "available" in path.name.lower():
            product_status = "available"

        file_stat = path.stat()
        base_metadata = {
            "source_filename": path.name,
            "relative_path": str(path.parent.relative_to(Path.cwd()))
            if Path.cwd() in path.parents
            else str(path.parent),
            "category": category,
            "classification_confidence": f"{confidence:.2f}",
            "classifier": "llm_semantic_with_cross_check",
            "processed_at": pd.Timestamp.utcnow().isoformat(),
            "file_creation_time": pd.Timestamp.fromtimestamp(file_stat.st_ctime).isoformat(),
            "file_modification_time": pd.Timestamp.fromtimestamp(file_stat.st_mtime).isoformat(),
            "file_size_bytes": file_stat.st_size,
            "document_entities": entities,
            "requires_manual_review": review_reason is not None,
            "review_reason": review_reason,
            "quarantined": False,
        }
        base_metadata[self.config.PRODUCT_STATUS_FIELD_NAME] = product_status

        chunker = self.chunker_map.get(category, self.chunker_map["default"])
        content_for_chunking = path if isinstance(chunker, StructuredDataExtractor) else Path(raw_text)
        chunks = chunker.chunk(content_for_chunking, document_id, base_metadata)

        def enrich_chunk(chunk):
            if not chunk.get("content") or chunk["content"].strip() in ("{}", "[]"):
                logger.warning(
                    f"Salto l'arricchimento per chunk vuoto/strutturato/JSON: {chunk.get('chunk_id', 'N/A')}"
                )
                return chunk
            is_json_content = False
            content_obj = None
            try:
                content_obj = json.loads(chunk["content"])
                if isinstance(content_obj, dict):
                    is_json_content = True
            except json.JSONDecodeError:
                pass

            if is_json_content:
                # Helper functions for safe value handling
                def safe_get(obj, key, formatter=None):
                    """Safely get and format a value from the object."""
                    value = obj.get(key)
                    if value is None or value == "":
                        return None
                    return formatter(value) if formatter else value

                def format_price(price):
                    """Format price with validation."""
                    try:
                        return f"{float(price):.2f}€"
                    except (ValueError, TypeError):
                        logger.warning(f"Prezzo non valido: {price}")
                        return None

                # Build summary parts
                summary_parts = []
                
                # Add description if available
                if desc := safe_get(content_obj, "description"):
                    summary_parts.append(desc)

                # Add serial if available
                if serial := safe_get(content_obj, "serial"):
                    summary_parts.append(f"Seriale: {serial}")

                # Add price if available and valid
                if price := safe_get(content_obj, "price", format_price):
                    summary_parts.append(f"Prezzo: {price}")

                # Add sheet name if available
                if sheet := safe_get(content_obj, "sheet_name"):
                    summary_parts.append(f"Foglio: {sheet}")
                # Add status if discontinued
                if content_obj and content_obj.get(PipelineConfig.PRODUCT_STATUS_FIELD_NAME) == "discontinued":
                    summary_parts.append("Stato: Discontinuato")

                # Set summary
                chunk["metadata"]["chunk_summary"] = (
                    ", ".join(summary_parts) if summary_parts else "Nessun dato significativo"
                )

                # Generate hypothetical questions
                hypothetical_questions = []

                def add_product_questions(identifier):
                    """Add standard product-related questions."""
                    if identifier:
                        hypothetical_questions.extend([
                            f"Qual è il prezzo di {identifier}?",
                            f"Qual è il seriale di {identifier}?",
                            f"È {identifier} discontinuato?",
                            f"Ci sono alternative per {identifier}?"
                        ])

                # Add questions based on available data
                if desc := safe_get(content_obj, "description"):
                    add_product_questions(desc)
                elif serial := safe_get(content_obj, "serial"):
                    add_product_questions(serial)
                    hypothetical_questions.extend([
                        f"Qual è la descrizione del prodotto con seriale {serial}?",
                        f"Quanto costa il prodotto {serial}?"
                    ])

                # Add sheet-specific question
                if sheet := safe_get(content_obj, "sheet_name"):
                    product_ref = (
                        safe_get(content_obj, "description") or 
                        safe_get(content_obj, "serial") or 
                        "questo prodotto"
                    )
                    hypothetical_questions.append(
                        f"A quale foglio appartiene {product_ref}?"
                    )
                # Add status-specific questions
                if content_obj and content_obj.get(PipelineConfig.PRODUCT_STATUS_FIELD_NAME) == "discontinued":
                    product_ref = (
                        safe_get(content_obj, "description") or 
                        safe_get(content_obj, "serial") or 
                        "questo prodotto"
                    )
                    hypothetical_questions.extend([
                        f"Ci sono alternative per {product_ref}?"
                    ])

                # Add fallback question if no specific questions were generated
                if not hypothetical_questions:
                    hypothetical_questions.append(
                        "Quali informazioni contiene questo record?"
                    )

                chunk["metadata"]["hypothetical_questions"] = hypothetical_questions
                return chunk
            enrichment_data = call_llm_for_enrichment(chunk["content"], client=primary_llm_client)
            if isinstance(enrichment_data, dict):
                chunk_summary = enrichment_data.get("chunk_summary", "Nessun riassunto fornito dall'LLM.")
                hypothetical_questions = enrichment_data.get("hypothetical_questions", [])
                chunk["metadata"]["chunk_summary"] = chunk_summary or "Nessun dato significativo"
                chunk["metadata"]["hypothetical_questions"] = (
                    hypothetical_questions or ["Qual è il contenuto di questo chunk?"]
                )
            else:
                logger.warning(
                    f"[⚠️ Arricchimento saltato] L'LLM ha restituito un tipo inatteso per l'arricchimento del chunk '{chunk.get('chunk_id', '<sconosciuto>')}'. Atteso dict, ricevuto {type(enrichment_data)}."
                )
                chunk["metadata"]["chunk_summary"] = chunk["content"][:200] + "..."
                chunk["metadata"]["hypothetical_questions"] = ["Contenuto non arricchito"]
            return chunk

        with concurrent.futures.ThreadPoolExecutor() as pool:
            enriched_chunks = list(pool.map(enrich_chunk, chunks))
        logger.info(f"Creati e arricchiti con successo {len(enriched_chunks)} chunk per '{path.name}'.")
        return enriched_chunks

    def run(self, input_path: Path) -> List[Dict[str, Any]]:
        all_chunks: List[Dict[str, Any]] = []
        files = self.scanner.scan(input_path)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_file = {executor.submit(self.process_file, file): file for file in files}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result_chunks = future.result()
                    if result_chunks:
                        all_chunks.extend(result_chunks)
                except Exception as e:  # pragma: no cover - log critical
                    logger.critical(
                        f"Errore critico durante l'elaborazione di '{file.name}': {e}", exc_info=True
                    )
                    self._quarantine_file(file, f"Errore critico della pipeline: {e}")
        self.scanner.cleanup()
        logger.info(f"Pipeline completata. Totale chunk generati: {len(all_chunks)}")
        return all_chunks
    
    def process_single_file(self, file_path: Path, category: str = None) -> bool:
        """
        Process a single file through the knowledge pipeline.
        
        Args:
            file_path: Path to the file to process
            category: Optional category override for the document
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            logger.info(f"Processing single file: {file_path.name}")
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Process the single file
            chunks = self.process_file(file_path)
            
            if not chunks:
                logger.warning(f"No chunks generated from file: {file_path.name}")
                return False
            
            # Override category if provided
            if category:
                for chunk in chunks:
                    chunk["metadata"]["category"] = category
                    logger.info(f"Set category to '{category}' for {file_path.name}")
            
            # Save processed chunks to output file
            output_path = Path(self.config.OUTPUT_FILE)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Append to existing file or create new one
            with open(output_path, "a", encoding="utf-8") as f:
                for chunk in chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False, indent=None) + "\n")
            
            logger.info(f"Successfully processed {file_path.name}: {len(chunks)} chunks generated")
            return True
            
        except Exception as e:
            logger.error(f"Error processing single file {file_path.name}: {e}", exc_info=True)
            self._quarantine_file(file_path, f"Error in single file processing: {e}")
            return False


def cli() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline di Ingestione della Conoscenza Parallela e Focalizzata sull'Affidabilità."
    )
    parser.add_argument("input_path", type=str, help="Percorso della directory o del file ZIP con i documenti.")
    parser.add_argument("--output", default="knowledge_base_reliable.jsonl", help="File di output JSON Lines.")
    args = parser.parse_args()

    config = PipelineConfig()
    pipeline = KnowledgePipeline(config)
    processed_chunks = pipeline.run(Path(args.input_path))
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in processed_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False, indent=None) + "\n")
    logger.info(f"Risultati salvati in: {output_path}")
    logger.info(
        f"I file che richiedono revisione manuale sono stati spostati nella directory '{config.QUARANTINE_DIR}'."
    )


if __name__ == "__main__":
    cli()
