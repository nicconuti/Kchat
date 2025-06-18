import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import pandas as pd

from .config import PipelineConfig
from .logging_config import setup_logging
from .llm_utils import call_llm_for_structured_extraction, primary_llm_client

logger = setup_logging()


class RecursiveCharacterTextSplitter:
    """Semplice splitter di testo ricorsivo basato su caratteri."""

    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 128, separators: Optional[List[str]] = None) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        final_chunks: List[str] = []
        queue = [text]
        for separator in self.separators:
            new_queue: List[str] = []
            for current_text in queue:
                if len(current_text) <= self.chunk_size:
                    new_queue.append(current_text)
                    continue
                parts = current_text.split(separator)
                temp_chunk: List[str] = []
                for part in parts:
                    if len(separator.join(temp_chunk + [part])) <= self.chunk_size:
                        temp_chunk.append(part)
                    else:
                        if temp_chunk:
                            new_queue.append(separator.join(temp_chunk))
                        temp_chunk = [part]
                if temp_chunk:
                    new_queue.append(separator.join(temp_chunk))
            queue = new_queue
        for chunk_candidate in queue:
            if len(chunk_candidate) > self.chunk_size:
                final_chunks.extend(self._split_with_overlap(chunk_candidate))
            else:
                final_chunks.append(chunk_candidate)
        return final_chunks

    def _split_with_overlap(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start += self.chunk_size - self.chunk_overlap
            start = min(start, len(text) - 1)
            if self.chunk_overlap > 0 and start == end:
                break
        return chunks


class ChunkingStrategy(Protocol):
    def chunk(self, content: Any, source_id: str, metadata: Dict) -> List[Dict[str, Any]]: ...


class AdvancedSemanticChunker(ChunkingStrategy):
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def chunk(self, text: str, source_id: str, metadata: Dict) -> List[Dict[str, Any]]:
        chunks = self.text_splitter.split_text(text)
        chunk_list = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = dict(metadata)
            chunk_list.append(
                {
                    "chunk_id": f"{source_id}#chunk{i:04d}",
                    "source_document_id": source_id,
                    "content": chunk_text,
                    "metadata": chunk_metadata,
                }
            )
        return chunk_list


class StructuredDataExtractor(ChunkingStrategy):
    def chunk(self, file_path: Path, source_id: str, metadata: Dict) -> List[Dict[str, Any]]:
        try:
            with pd.ExcelFile(file_path) as xls:
                all_records: List[Dict[str, Any]] = []
                for sheet_name in xls.sheet_names:
                    df = xls.parse(sheet_name).head(PipelineConfig.TABLE_PREVIEW_ROWS)
                    extracted_records_from_sheet = call_llm_for_structured_extraction(
                        df.to_string(index=False),
                        sheet_name,
                        client=primary_llm_client,
                    )
                    for record in extracted_records_from_sheet:
                        record["sheet_name"] = sheet_name
                        if "discontinued" in sheet_name.lower():
                            record[PipelineConfig.PRODUCT_STATUS_FIELD_NAME] = "discontinued"
                        else:
                            record[PipelineConfig.PRODUCT_STATUS_FIELD_NAME] = "active"
                    all_records.extend(extracted_records_from_sheet)
            chunk_list = []
            for i, rec in enumerate(all_records):
                chunk_metadata = dict(metadata)
                chunk_list.append(
                    {
                        "chunk_id": f"{source_id}#row{i:04d}",
                        "source_document_id": source_id,
                        "content": json.dumps(rec, ensure_ascii=False),
                        "metadata": chunk_metadata,
                    }
                )
            return chunk_list
        except Exception:  # pragma: no cover - log errors
            logger.error(f"Errore durante il chunking dei dati strutturati da '{file_path.name}'.", exc_info=True)
            return []
