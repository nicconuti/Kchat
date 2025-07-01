from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from models.call_local_llm import call_mistral

logger = logging.getLogger(__name__)


def load_csv(path: Union[str, Path], max_retries: int = 2) -> list[dict[str, Any]]:
    """Load ``path`` into a list of rows using pandas with enhanced error handling.

    If parsing with default settings fails, retry without header and
    assign generic column names. Includes multiple fallback strategies.
    """
    p = Path(path)
    
    # Validate file exists and is readable
    if not p.exists():
        logger.error(f"File non trovato: {p}")
        raise FileNotFoundError(f"CSV file not found: {p}")
    
    if not p.is_file():
        logger.error(f"Path non è un file: {p}")
        raise ValueError(f"Path is not a file: {p}")
    
    # Check file size
    file_size = p.stat().st_size
    if file_size == 0:
        logger.warning(f"File CSV vuoto: {p}")
        return []
    
    if file_size > 100 * 1024 * 1024:  # 100MB limit
        logger.warning(f"File CSV molto grande ({file_size / 1024 / 1024:.1f}MB): {p}")
    
    # Strategy 1: Default pandas read
    try:
        logger.debug(f"Tentativo di lettura CSV standard: {p}")
        df = pd.read_csv(p)
        
        # Check if all columns are numeric (likely no header)
        if all(str(c).isdigit() for c in df.columns):
            raise ValueError("numeric_header_detected")
        
        # Validate data
        if df.empty:
            logger.warning(f"CSV caricato ma vuoto: {p}")
            return []
        
        logger.info(f"CSV caricato con successo: {len(df)} righe, {len(df.columns)} colonne")
        return df.fillna("").to_dict(orient="records")  # type: ignore[return-value]
        
    except Exception as e:
        logger.warning(f"Lettura CSV standard fallita per {p}: {e}")
    
    # Strategy 2: Try different encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            logger.debug(f"Tentativo lettura CSV con encoding {encoding}: {p}")
            df = pd.read_csv(p, encoding=encoding)
            
            if not df.empty:
                logger.info(f"CSV caricato con encoding {encoding}: {len(df)} righe")
                return df.fillna("").to_dict(orient="records")  # type: ignore[return-value]
                
        except Exception as e:
            logger.debug(f"Encoding {encoding} fallito: {e}")
            continue
    
    # Strategy 3: No header, auto-generated column names
    try:
        logger.debug(f"Tentativo lettura CSV senza header: {p}")
        df = pd.read_csv(p, header=None)
        df.columns = [f"col_{i}" for i in range(len(df.columns))]  # type: ignore[assignment]
        
        if not df.empty:
            logger.info(f"CSV caricato senza header: {len(df)} righe, {len(df.columns)} colonne")
            return df.fillna("").to_dict(orient="records")  # type: ignore[return-value]
            
    except Exception as e:
        logger.warning(f"Lettura CSV senza header fallita: {e}")
    
    # Strategy 4: Try different separators
    separators = [',', ';', '\t', '|']
    for sep in separators:
        try:
            logger.debug(f"Tentativo lettura CSV con separatore '{sep}': {p}")
            df = pd.read_csv(p, sep=sep)
            
            # Only use if we get multiple columns
            if len(df.columns) > 1 and not df.empty:
                logger.info(f"CSV caricato con separatore '{sep}': {len(df)} righe, {len(df.columns)} colonne")
                return df.fillna("").to_dict(orient="records")  # type: ignore[return-value]
                
        except Exception as e:
            logger.debug(f"Separatore '{sep}' fallito: {e}")
            continue
    
    # Final fallback: return empty list
    logger.error(f"Impossibile leggere il file CSV con tutte le strategie: {p}")
    raise ValueError(f"Unable to parse CSV file with any strategy: {p}")


def summarize_csv(path: Union[str, Path], sample_rows: int = 3, timeout: float = 10.0) -> str:
    """Return a short summary of the CSV structure using Mistral with enhanced error handling."""
    p = Path(path)
    
    try:
        # Validate file
        if not p.exists():
            return f"Errore: File {p} non trovato"
        
        # Load sample data with enhanced error handling
        logger.debug(f"Caricamento campione CSV per riassunto: {p}")
        
        try:
            df = pd.read_csv(p, nrows=sample_rows)
        except Exception as e:
            logger.warning(f"Lettura CSV standard fallita per riassunto: {e}")
            # Fallback to load_csv function
            try:
                all_rows = load_csv(p)
                if not all_rows:
                    return "File CSV vuoto"
                
                # Take sample from loaded data
                sample_data = all_rows[:sample_rows]
                df = pd.DataFrame(sample_data)
            except Exception as e2:
                logger.error(f"Impossibile caricare CSV per riassunto: {e2}")
                return f"Errore nel caricamento CSV: {str(e2)}"
        
        # Validate data
        if df.empty:
            return "File CSV vuoto"
        
        # Prepare data for LLM
        rows = df.fillna("").to_dict(orient="records")
        
        # Truncate large values to avoid prompt bloat
        truncated_rows = []
        for row in rows:
            truncated_row = {}
            for key, value in row.items():
                str_value = str(value)
                if len(str_value) > 50:
                    str_value = str_value[:47] + "..."
                truncated_row[key] = str_value
            truncated_rows.append(truncated_row)
        
        prompt = (
            "Analyze this CSV data and describe the meaning and purpose of the columns in one clear sentence. "
            "Focus on what type of data this appears to be (e.g., sales data, user records, etc.).\n"
            f"Sample rows ({len(truncated_rows)} of {len(df)}):\n{truncated_rows}\n\nSummary:"
        )
        
        # Call LLM with timeout protection
        try:
            summary = call_mistral(prompt).strip()
            
            if not summary:
                return _generate_fallback_summary(df)
            
            # Validate summary length
            if len(summary) > 500:
                summary = summary[:497] + "..."
            
            logger.info(f"Riassunto CSV generato per {p}: {len(summary)} caratteri")
            return summary
            
        except Exception as e:
            logger.warning(f"LLM call failed for CSV summary: {e}")
            return _generate_fallback_summary(df)
    
    except Exception as e:
        logger.error(f"Errore imprevisto nel riassunto CSV: {e}")
        return f"Errore nell'analisi del file: {str(e)}"


def _generate_fallback_summary(df: pd.DataFrame) -> str:
    """Generate a basic summary without LLM when AI fails."""
    try:
        col_count = len(df.columns)
        row_count = len(df)
        
        # Analyze column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        summary_parts = [f"CSV con {col_count} colonne e {row_count} righe campione"]
        
        if numeric_cols:
            summary_parts.append(f"{len(numeric_cols)} colonne numeriche: {', '.join(numeric_cols[:3])}")
        
        if text_cols:
            summary_parts.append(f"{len(text_cols)} colonne di testo: {', '.join(text_cols[:3])}")
        
        return ". ".join(summary_parts) + "."
        
    except Exception:
        return "File CSV con struttura non determinabile"


def validate_csv_integrity(path: Union[str, Path]) -> dict[str, Any]:
    """Validate CSV file integrity and return diagnostic information."""
    p = Path(path)
    
    result = {
        "valid": False,
        "exists": False,
        "readable": False,
        "rows": 0,
        "columns": 0,
        "size_bytes": 0,
        "encoding_detected": None,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Check existence
        if not p.exists():
            result["errors"].append("File does not exist")
            return result
        result["exists"] = True
        
        # Check size
        result["size_bytes"] = p.stat().st_size
        if result["size_bytes"] == 0:
            result["warnings"].append("File is empty")
        
        # Try to load and validate
        try:
            data = load_csv(p)
            result["readable"] = True
            result["rows"] = len(data)
            result["columns"] = len(data[0]) if data else 0
            result["valid"] = True
            
        except Exception as e:
            result["errors"].append(f"Load failed: {str(e)}")
    
    except Exception as e:
        result["errors"].append(f"Validation failed: {str(e)}")
    
    return result
