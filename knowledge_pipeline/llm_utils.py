import json
import re
import subprocess
import time
from functools import wraps
from typing import Any, Callable, Dict, List

from models._call_llm import LLMClient, ModelName
from .logging_config import setup_logging
from prompts import LLMPrompts

logger = setup_logging()

# Inizializza due client LLM separati per classificazione primaria e fallback
primary_llm_client = LLMClient(default_model="deepseek-r1:14b")
fallback_llm_client = LLMClient(default_model="mistral")


def resilient_llm_call(retries: int = 3, delay: int = 5) -> Callable:
    """Decoratore per aggiungere logica di retry alle chiamate LLM."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if result is not None and (
                        (isinstance(result, dict) and result)
                        or (isinstance(result, list) and result)
                        or (isinstance(result, str) and result.strip())
                    ):
                        return result
                    logger.warning(
                        f"Tentativo {attempt}/{retries}: Chiamata LLM vuota. Riprovo tra {delay}s per {func.__name__}..."
                    )
                except subprocess.CalledProcessError as e:
                    logger.error(
                        f"Tentativo {attempt}/{retries}: Subprocess fallito con codice {e.returncode}.", exc_info=True
                    )
                except Exception:
                    logger.error(
                        f"Tentativo {attempt}/{retries}: eccezione imprevista per {func.__name__}.",
                        exc_info=True,
                    )
                time.sleep(delay)
            logger.critical(
                f"Tutti i {retries} tentativi falliti per {func.__name__}. Restituisco valore vuoto di default."
            )
            if "structured_extraction" in func.__name__:
                return []
            if "classification" in func.__name__ or "enrichment" in func.__name__:
                return {}
            return ""

        return wrapper

    return decorator


def _parse_llm_json_output(raw_output: str) -> Any:
    """Parsa in modo sicuro il JSON da un output LLM raw."""
    if raw_output is None or not isinstance(raw_output, str) or not raw_output.strip():
        logger.warning("Input to _parse_llm_json_output was None or empty")
        return {}
    try:
        match = re.search(r"```json\s*([\s\S]+?)\s*```", raw_output)
        if match:
            return json.loads(match.group(1))
        raw_output = raw_output.strip()
        if (raw_output.startswith("{") and raw_output.endswith("}")) or (
            raw_output.startswith("[") and raw_output.endswith("]")
        ):
            return json.loads(raw_output)
        return {}
    except json.JSONDecodeError as e:
        logger.warning(
            f"Impossibile decodificare JSON dall'output LLM: '{raw_output[:100]}...'. Errore: {e}"
        )
        return {}


@resilient_llm_call()
def call_llm_for_classification(
    text_preview: str,
    filename: str,
    categories_with_desc: Dict,
    model: ModelName,
    client: LLMClient = primary_llm_client,
) -> Dict[str, Any]:
    """Chiama un LLM specifico per la classificazione zero-shot."""
    logger.info(f"Uso '{model}' per la classificazione semantica di '{filename}'...")
    prompt = LLMPrompts.get_classification_prompt(categories_with_desc, filename, text_preview)
    full_response_content = ""
    if model.startswith("deepseek"):
        logger.info(
            f"Risposta in streaming da Deepseek per '{filename}' - output live qui sotto:"
        )
        print(f"\n--- Stream di Risposta LLM per {filename} ({model}) ---\n")
        for chunk_text in client.stream(prompt, model=model, print_live=True):
            full_response_content += chunk_text
        print("\n--- Fine Stream di Risposta LLM ---\n")
    else:
        raw_response = client.call(prompt, model=model)
        full_response_content = raw_response
        logger.info(f"Risposta LLM per {filename}:\n{raw_response}\n")

    parsed = _parse_llm_json_output(full_response_content)
    reasoning = parsed.get("reasoning")
    if not reasoning:
        match = re.search(r"Reasoning:\s*(.*?)(?=\n```json|$)", full_response_content, re.IGNORECASE | re.DOTALL)
        if match:
            reasoning = match.group(1).strip()
        else:
            reasoning = "Nessun ragionamento fornito."
    parsed["reasoning"] = reasoning
    if "confidence" not in parsed:
        parsed["confidence"] = 0.0
        logger.warning(
            f"La risposta LLM per {filename} non includeva 'confidence'. Imposto a 0.0."
        )
    return parsed


@resilient_llm_call()
def validate_record_with_llm(record: Dict[str, Any], client: LLMClient = primary_llm_client) -> Dict[str, Any]:
    """
    Valida un record strutturato tramite il LLM per correggere errori o incompletezze.
    """
    try:
        prompt_text = LLMPrompts.PROMPT_VALIDATE_EXCEL_RECORD.format(**record)

        raw_response = client.call(
            prompt=prompt_text,
            model="deepseek-r1:14b"
        )

        # Parse the LLM response which comes as a string
        if not isinstance(raw_response, str) or not raw_response.strip():
            logger.warning(f"Risposta LLM vuota o non valida: {raw_response}")
            return record

        # Parse JSON from LLM response
        parsed_response = _parse_llm_json_output(raw_response)
        
        if not isinstance(parsed_response, dict):
            logger.warning(f"Impossibile parsare la risposta LLM come JSON: {raw_response}")
            return record

        # Validate and construct corrected record
        corrected_record = {
            "serial": parsed_response.get("serial", record.get("serial")),
            "description": parsed_response.get("description", record.get("description")),
            "price": parsed_response.get("price", record.get("price")),
            "sheet_name": record.get("sheet_name"),
            "product_status": record.get("product_status"),
        }
        
        # Log validation changes if any
        changes = []
        for key in ["serial", "description", "price"]:
            if corrected_record[key] != record.get(key):
                changes.append(f"{key}: {record.get(key)} -> {corrected_record[key]}")
        
        if changes:
            logger.info(f"LLM validation made changes: {', '.join(changes)}")
        
        return corrected_record

    except Exception as e:
        logger.error("Errore nella validazione record con LLM", exc_info=True)
        return record

@resilient_llm_call()
def call_llm_for_enrichment(
    chunk_text: str,
    client: LLMClient = primary_llm_client,
) -> Dict[str, Any]:
    """Arricchisce un chunk con riassunto e domande ipotetiche."""
    logger.info(f"Uso 'deepseek' per l'arricchimento del chunk: '{chunk_text[:50]}...'")
    prompt = LLMPrompts.get_enrichment_prompt(chunk_text)
    raw_response = client.call(prompt, model="deepseek-r1:14b")
    return _parse_llm_json_output(raw_response)
