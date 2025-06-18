import re
import json
import argparse
import pandas as pd
import spacy
import subprocess
import time
import shutil
import logging
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional, Protocol, Callable
from functools import lru_cache, wraps
from tempfile import TemporaryDirectory
import zipfile
# Assumendo che il modulo 'prompts' esista e contenga le definizioni dei prompt necessarie
from prompts import LLMPrompts 
import pdfplumber
import docx

# Assumendo che il modulo 'models' esista e contenga la classe LLMClient
from models._call_llm import LLMClient, ModelName 

# --- 1. CONFIGURAZIONE DEL LOGGING STRUTTURATO ---

class JsonFormatter(logging.Formatter):
    """Formattatore JSON personalizzato per log strutturati."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "pid": record.process,
            "thread": record.threadName, # Aggiunto il nome del thread per un migliore debug in processi paralleli
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    """Configura il logger root per l'output JSON strutturato."""
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    # Evita di aggiungere handler duplicati in processi paralleli
    # Controlla se un handler con lo stesso tipo di formattatore è già presente
    if not any(isinstance(h.formatter, JsonFormatter) for h in log.handlers):
        log.addHandler(handler)
    return log

logger = setup_logging()

# --- 2. CONFIGURAZIONE CENTRALE ---

class PipelineConfig:
    """Configurazioni per la pipeline di ingestione."""
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".html", ".htm", ".csv", ".json", ".xml"}
    
    SEMANTIC_CATEGORIES = {
        "product_price": "Documenti contenenti listini prezzi, offerte commerciali, preventivi o analisi costi.",
        "product_guide": "Manuali tecnici, guide utente, istruzioni di installazione o specifiche di prodotto.",
        "tech_assistance": "Rapporti di errore, guide alla risoluzione dei problemi, richieste di supporto tecnico o analisi dei problemi.",
        "software_assistance": "Guide all'installazione del software, procedure di aggiornamento, informazioni sulla licenza o problemi relativi al software.",
        "unclassified": "Documenti che non rientrano in nessuna delle altre categorie."
    }
    
    MIN_EXTRACTED_TEXT_SIZE = 50
    FULL_TEXT_CLASSIFICATION_LIMIT = 8000 
    TABLE_PREVIEW_ROWS = 100

    # Configurazione del chunking
    CHUNK_SIZE = 1024
    CHUNK_OVERLAP = 128

    # Soglie di affidabilità
    LLM_CLASSIFICATION_THRESHOLD = 0.80
    CROSS_CHECK_CONFIDENCE_THRESHOLD = 0.95 

    QUARANTINE_DIR = "quarantine"
    PRODUCT_STATUS_FIELD_NAME = "product_status" # Nuovo campo per lo stato esplicito del prodotto

# --- 3. INTEGRAZIONE LLM CON RESILIENZA ---

# Inizializza LLMClient globalmente (per semplicità in questo esempio)
llm_client = LLMClient(default_model="mistral") 

def resilient_llm_call(retries=3, delay=5):
    """Decoratore per aggiungere logica di retry alle chiamate LLM con gestione errori più specifica."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    result = func(*args, **kwargs)
                    # Controlla se il risultato non è None e non è vuoto/blank in base al tipo
                    if result is not None and (isinstance(result, dict) and result != {} or 
                                               isinstance(result, list) and result != [] or 
                                               isinstance(result, str) and result.strip() != ""):
                        return result
                    logger.warning(f"Tentativo {attempt}/{retries}: Chiamata LLM ha restituito vuoto/None/stringa vuota. Riprovo tra {delay}s per {func.__name__}...")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Tentativo {attempt}/{retries}: Il sottoprocesso è fallito con codice di uscita {e.returncode}. Stderr: {e.stderr}", exc_info=True)
                except Exception:
                    logger.error(f"Tentativo {attempt}/{retries}: Si è verificata un'eccezione imprevista per {func.__name__}.", exc_info=True)
                time.sleep(delay)
            logger.critical(f"Tutti i {retries} tentativi sono falliti per la funzione {func.__name__}. Restituisco un valore vuoto di default.")
            # Restituisce un valore vuoto appropriato in base al tipo di ritorno atteso della funzione
            if 'structured_extraction' in func.__name__:
                return []
            elif 'classification' in func.__name__ or 'enrichment' in func.__name__:
                return {}
            return "" # Default per testo raw/stringa
        return wrapper
    return decorator

def _parse_llm_json_output(raw_output: str) -> Any: # Changed return type hint to Any for flexibility
    """Parsa in modo sicuro il JSON da un output LLM raw."""
    if raw_output is None or not isinstance(raw_output, str) or raw_output.strip() == "": # Added explicit check for None, non-string, and empty string
        logger.warning("Input to _parse_llm_json_output was None, not a string, or empty. Returning empty dict.")
        return {} # Default to empty dict
    
    try:
        # Prioritizza la ricerca di un blocco JSON markdown (```json ... ```)
        match = re.search(r'```json\s*([\s\S]+?)\s*```', raw_output)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        
        # Se nessun blocco JSON markdown, prova a parsare l'intera stringa come JSON se assomiglia a uno
        raw_output = raw_output.strip()
        # This part should be robust to single objects vs. arrays directly.
        if (raw_output.startswith('{') and raw_output.endswith('}')) or \
           (raw_output.startswith('[') and raw_output.endswith(']')):
            return json.loads(raw_output)
        
        return {}
    except json.JSONDecodeError as e:
        logger.warning(f"Impossibile decodificare JSON dall'output LLM: '{raw_output[:100]}...'. Errore: {e}")
        return {}

@resilient_llm_call()
def call_llm_for_classification(text_preview: str, filename: str, categories_with_desc: Dict, model: ModelName) -> Dict[str, Any]:
    """Chiama un LLM specifico per la classificazione zero-shot usando il Chain-of-Thought."""
    logger.info(f"Uso '{model}' per la classificazione semantica di '{filename}'...")
    prompt = LLMPrompts.get_classification_prompt(categories_with_desc, filename, text_preview)
    
    full_response_content = ""
    # Se il modello è Deepseek, chiama lo stream con print_live=True
    if model.startswith("deepseek"):
        logger.info(f"Risposta in streaming da Deepseek per '{filename}' - output live qui sotto:")
        print(f"\n--- Stream di Risposta LLM per {filename} ({model}) ---\n") 
        for chunk_text in llm_client.stream(prompt, model=model, print_live=True):
            full_response_content += chunk_text
        print("\n--- Fine Stream di Risposta LLM ---\n")
        
    else:
        # Per altri modelli, usa la chiamata bloccante
        raw_response = llm_client.call(prompt, model=model)
        full_response_content = raw_response
        logger.info(f"Risposta LLM per {filename}:\n{raw_response}\n")
    
    parsed = _parse_llm_json_output(full_response_content)
    
    reasoning = "Nessun ragionamento fornito."
    if "reasoning" in parsed:
        reasoning = parsed["reasoning"]
    else:
        reasoning_match = re.search(r'Reasoning:\s*(.*?)(?=\n```json|$)', full_response_content, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
    
    parsed["reasoning"] = reasoning 
    logger.info(f"Ragionamento di classificazione LLM per '{filename}': {reasoning}")

    if "confidence" not in parsed:
        parsed["confidence"] = 0.0 
        logger.warning(f"La risposta LLM per {filename} non includeva 'confidence'. Imposto a 0.0.")

    return parsed

@resilient_llm_call()
def call_llm_for_structured_extraction(sheet_preview: str, sheet_name: str) -> List[Dict[str, Any]]:
    """Chiama 'deepseek' per estrarre dati strutturati da un foglio Excel.
    Si aspetta che LLMClient.call_json gestisca il parsing JSON e restituisca una lista/dict o None."""
    logger.info(f"Uso 'deepseek' per l'estrazione strutturata dal foglio '{sheet_name}'...")
    prompt = LLMPrompts.get_structured_extraction_prompt(sheet_preview, sheet_name)
    
    # llm_client.call_json dovrebbe restituire un oggetto Python (lista o dict) o None in caso di fallimento.
    raw_parsed_data = llm_client.call_json(prompt, model="deepseek-r1:14b") 
    
    # Gestione esplicita di None o tipi inattesi da llm_client.call_json
    if raw_parsed_data is None:
        logger.warning(f"llm_client.call_json ha restituito None per l'estrazione strutturata del foglio '{sheet_name}'. Questo di solito significa che l'LLM non ha fornito un JSON parsabile.")
        return [] # Ritorna lista vuota per il retry

    parsed_json: List[Dict[str, Any]] = []
    if isinstance(raw_parsed_data, list):
        parsed_json = raw_parsed_data
    elif isinstance(raw_parsed_data, dict):
        # Se l'LLM ha restituito un singolo oggetto invece di un array, lo avvolgiamo in una lista.
        logger.warning(f"LLM ha restituito un singolo oggetto JSON invece di un array per l'estrazione strutturata. Lo avvolgo in una lista per il foglio '{sheet_name}'.")
        parsed_json = [raw_parsed_data]
    else:
        logger.warning(f"LLM per l'estrazione strutturata ha restituito un tipo inatteso: {type(raw_parsed_data)}. Atteso lista o dict. Ricevuto: {raw_parsed_data}. Ritorno lista vuota.")
        return []

    validated_list = []
    for item in parsed_json:
        if isinstance(item, dict) and all(key in item for key in ["serial", "description", "price"]):
            if "price" in item and item["price"] is not None:
                try:
                    item["price"] = float(item["price"])
                except (ValueError, TypeError):
                    logger.warning(f"Valore prezzo non valido incontrato per seriale {item.get('serial', 'N/A')}: {item['price']}. Imposto a null.")
                    item["price"] = None 
            # Aggiungi il nome del foglio a ogni elemento estratto per il contesto
            item['sheet_name'] = sheet_name 
            validated_list.append(item)
        else:
            logger.warning(f"Elemento malformato saltato dall'output LLM di estrazione strutturata: {item}")
    return validated_list
    
@resilient_llm_call()
def call_llm_for_enrichment(chunk_text: str) -> Dict[str, Any]:
    """Chiama 'deepseek' per arricchire un chunk con un riassunto e domande ipotetiche.
    Sottolinea che il riassunto e le domande devono essere derivate SOLO dal testo fornito."""
    logger.info(f"Uso 'deepseek' per l'arricchimento del chunk: '{chunk_text[:50]}...'")
    prompt = LLMPrompts.get_enrichment_prompt(chunk_text) # Questo prompt deve essere aggiornato per le istruzioni
    
    # Utilizzo _parse_llm_json_output per gestire la risposta LLM generica
    raw_response = llm_client.call(prompt, model="deepseek-r1:14b")
    return _parse_llm_json_output(raw_response)


# --- 4. COMPONENTI DELLA PIPELINE ---

class FileScanner:
    """Scansiona ricorsivamente una directory, un singolo file o un file ZIP per file idonei."""
    def __init__(self, extensions: set):
        self.supported_extensions = extensions
        self._temp_dir: Optional[TemporaryDirectory] = None

    def scan(self, path: Path) -> List[Path]:
        logger.info(f"Avvio scansione in: {path}")
        files_to_process = []
        if path.is_file():
            if path.suffix.lower() == ".zip":
                self._temp_dir = TemporaryDirectory()
                zip_base_path = Path(self._temp_dir.name)
                logger.info(f"Estrazione file ZIP in directory temporanea: {zip_base_path}")
                with zipfile.ZipFile(path, 'r') as zf:
                    zf.extractall(zip_base_path)
                files_to_process = list(zip_base_path.rglob("*"))
            elif path.suffix.lower() in self.supported_extensions:
                files_to_process = [path]
            else: # Aggiunto per tipi di file singoli non supportati
                logger.warning(f"Il singolo file '{path.name}' ha un'estensione non supportata '{path.suffix.lower()}'. Saltato.")
                return []
        elif path.is_dir():
            files_to_process = list(path.rglob("*"))
        else:
            logger.error(f"Il percorso di input '{path}' non è né un file né una directory. Esco.")
            return []
        
        supported_files = [f for f in files_to_process if f.is_file() and f.suffix.lower() in self.supported_extensions]
        logger.info(f"Trovati {len(supported_files)} file supportati.")
        return supported_files
    
    def cleanup(self):
        if self._temp_dir:
            logger.info(f"Pulizia directory temporanea: {self._temp_dir.name}")
            self._temp_dir.cleanup()

class TextExtractor:
    """Estrae testo raw da vari formati di file, ottimizzato per file di grandi dimensioni."""
    def extract(self, path: Path, min_size: int, preview_rows: int) -> str:
        logger.info(f"Estrazione testo da: {path.name}")
        text = ""
        try:
            ext = path.suffix.lower()
            if ext == ".pdf":
                with pdfplumber.open(path) as pdf:
                    all_text = [page.extract_text() for page in pdf.pages if page.extract_text()]
                text = "\n".join(all_text)
            elif ext == ".docx":
                doc = docx.Document(path)
                all_text = [para.text for para in doc.paragraphs if para.text.strip()]
                text = "\n".join(all_text)
            elif ext == ".xlsx":
                # Per XLSX, l'estrazione del testo è principalmente per l'anteprima di classificazione
                # StructuredDataExtractor gestisce l'estrazione effettiva dei dati per il chunking
                with pd.ExcelFile(path) as xls:
                    all_sheet_previews = []
                    for sheet_name in xls.sheet_names:
                        try:
                            df = xls.parse(sheet_name).head(preview_rows)
                            all_sheet_previews.append(f"--- Foglio: {sheet_name} ---\n{df.to_string(index=False)}")
                        except Exception as e:
                            logger.warning(f"Impossibile parsare il foglio '{sheet_name}' da '{path.name}': {e}")
                    text = "\n\n".join(all_sheet_previews)
            elif ext == ".csv":
                df = pd.read_csv(path, nrows=preview_rows)
                text = df.to_string(index=False)
            elif ext in [".json", ".xml", ".txt", ".html", ".htm"]:
                text = path.read_text(encoding='utf-8', errors='ignore')
            
            return "" if len(text.strip()) < min_size else text
        except Exception:
            logger.error(f"Errore durante l'estrazione del testo da '{path.name}'.", exc_info=True)
            return ""

class EntityExtractor:
    """Estrae entità nominate dal testo usando SpaCy e filtra i termini generici."""
    @lru_cache(maxsize=1)
    def _get_nlp(self):
        logger.info("Caricamento del modello SpaCy 'xx_ent_wiki_sm'...")
        try: return spacy.load("xx_ent_wiki_sm")
        except OSError:
            logger.warning("Modello SpaCy 'xx_ent_wiki_sm' non trovato. Scarico...")
            spacy.cli.download("xx_ent_wiki_sm")
            return spacy.load("xx_ent_wiki_sm")

    def extract(self, text: str) -> List[str]:
        nlp = self._get_nlp()
        doc = nlp(text)
        
        # Definisci un set di parole comuni e meno informative da filtrare
        noisy_terms = {"nan", "price", "description", "serial", "module", "board", "amplifier", 
                       "watt", "inch", "ohm", "ch", "new", "empty", "full", "pcs", "model", 
                       "list", "total", "category", "number", "code", "part", "component", 
                       "interface", "panel", "rack", "logo", "i", "ii", "iii", "v", "l", "s",
                       "to", "be", "used", "with", "from", "until", "for", "with", "a", "an", "the", "and"} # Aggiunti più termini generici
        
        entities = set()
        for ent in doc.ents:
            entity_text = ent.text.strip()
            # Filtra per etichetta, lunghezza e contro i termini generici
            if ent.label_ in {"ORG", "PRODUCT", "WORK_OF_ART", "MISC"} and \
               len(entity_text) > 2 and \
               entity_text.lower() not in noisy_terms:
                
                # Ulteriore raffinamento per rimuovere artefatti numerici/newline se appaiono come entità
                if not re.fullmatch(r'(\d+|\n|\s)+', entity_text): 
                    entities.add(entity_text)
        
        logger.info(f"Estratti {len(entities)} entità uniche e filtrate.")
        return sorted(list(entities)) 

# --- 5. STRATEGIE DI CHUNKING AVANZATE ---
class RecursiveCharacterTextSplitter:
    """Implementazione semplificata di uno splitter di testo ricorsivo basato su caratteri."""
    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 128, separators: Optional[List[str]] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""] 

    def split_text(self, text: str) -> List[str]:
        """Divide il testo in chunk, cercando di rispettare i separatori e la dimensione del chunk."""
        final_chunks = []
        queue = [text] 

        for separator in self.separators:
            new_queue = []
            for current_text in queue:
                if len(current_text) <= self.chunk_size:
                    new_queue.append(current_text)
                    continue

                parts = current_text.split(separator)
                temp_chunk = []
                for part in parts:
                    # Controlla se l'aggiunta della parte corrente mantiene il chunk entro la dimensione
                    if len(separator.join(temp_chunk + [part])) <= self.chunk_size:
                        temp_chunk.append(part)
                    else:
                        # Se il chunk temporaneo non è vuoto, lo aggiunge
                        if temp_chunk:
                            new_queue.append(separator.join(temp_chunk))
                        temp_chunk = [part] # Inizia un nuovo chunk con la parte corrente
                if temp_chunk: 
                    new_queue.append(separator.join(temp_chunk))
            queue = new_queue
        
        # Passaggio finale per assicurarsi che tutti i chunk rispettino la dimensione massima, usando l'overlap se necessario
        for chunk_candidate in queue:
            if len(chunk_candidate) > self.chunk_size:
                final_chunks.extend(self._split_with_overlap(chunk_candidate))
            else:
                final_chunks.append(chunk_candidate)
        
        return final_chunks

    def _split_with_overlap(self, text: str) -> List[str]:
        """Funzione di supporto per dividere un singolo chunk grande con overlap se necessario."""
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
            if self.chunk_overlap > 0 and start == end: # Evita loop infiniti se chunk_size == chunk_overlap
                break
        return chunks

class ChunkingStrategy(Protocol):
    def chunk(self, content: Any, source_id: str, metadata: Dict) -> List[Dict[str, Any]]: ...

class AdvancedSemanticChunker(ChunkingStrategy):
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def chunk(self, text: str, source_id: str, metadata: Dict) -> List[Dict[str, Any]]:
        chunks = self.text_splitter.split_text(text) 
        
        chunk_list = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = dict(metadata) 
            chunk_list.append({
                "chunk_id": f"{source_id}#chunk{i:04d}", 
                "source_document_id": source_id,
                "content": chunk_text,
                "metadata": chunk_metadata
            })
        return chunk_list

class StructuredDataExtractor(ChunkingStrategy):
    def chunk(self, file_path: Path, source_id: str, metadata: Dict) -> List[Dict[str, Any]]:
        try:
            with pd.ExcelFile(file_path) as xls:
                all_records = []
                for sheet_name in xls.sheet_names:
                    df = xls.parse(sheet_name).head(PipelineConfig.TABLE_PREVIEW_ROWS)
                    
                    extracted_records_from_sheet = call_llm_for_structured_extraction(df.to_string(index=False), sheet_name)
                    
                    for record in extracted_records_from_sheet:
                        record['sheet_name'] = sheet_name
                        # Imposta lo stato del prodotto in base al nome del foglio
                        if "discontinued" in sheet_name.lower(): 
                            record[PipelineConfig.PRODUCT_STATUS_FIELD_NAME] = "discontinued"
                        else:
                            record[PipelineConfig.PRODUCT_STATUS_FIELD_NAME] = "active"
                        
                    all_records.extend(extracted_records_from_sheet)

            chunk_list = []
            for i, rec in enumerate(all_records):
                chunk_metadata = dict(metadata) 
                chunk_list.append({
                    "chunk_id": f"{source_id}#row{i:04d}", 
                    "source_document_id": source_id,
                    "content": json.dumps(rec, ensure_ascii=False), # Il contenuto è la stringa JSON del record
                    "metadata": chunk_metadata
                })
            return chunk_list
        except Exception:
            logger.error(f"Errore durante il chunking dei dati strutturati da '{file_path.name}'.", exc_info=True)
            return []

# --- 6. ORCHESTRATORE DELLA PIPELINE ---
class KnowledgePipeline:
    """Orchestra il processo di ingestione con focus su affidabilità e parallelismo."""
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.scanner = FileScanner(config.SUPPORTED_EXTENSIONS)
        self.text_extractor = TextExtractor()
        self.entity_extractor = EntityExtractor()
        self.chunker_map: Dict[str, ChunkingStrategy] = {
            "product_price": StructuredDataExtractor(),
            "default": AdvancedSemanticChunker(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP
            )
        }
        for cat in config.SEMANTIC_CATEGORIES:
            if cat not in self.chunker_map: self.chunker_map[cat] = self.chunker_map["default"]
        self.quarantine_path = Path(config.QUARANTINE_DIR)
        self.quarantine_path.mkdir(exist_ok=True)

    def _quarantine_file(self, file_path: Path, reason: str):
        try:
            self.quarantine_path.mkdir(parents=True, exist_ok=True)
            
            quarantine_target = self.quarantine_path / f"{pd.Timestamp.utcnow().strftime('%Y%m%d%H%M%S')}_{file_path.name}"
            logger.warning(f"Metto in quarantena il file '{file_path.name}'. Motivo: {reason}")
            shutil.copy(str(file_path), str(quarantine_target))
            with open(self.quarantine_path / f"{quarantine_target.name}.reason.log", "w", encoding='utf-8') as f:
                f.write(f"File in quarantena a {pd.Timestamp.utcnow().isoformat()}\nMotivo: {reason}\nPercorso originale: {file_path}\n")
        except Exception:
            logger.critical(f"Impossibile mettere in quarantena il file {file_path.name}. Richiede intervento manuale.", exc_info=True)

    def process_file(self, path: Path) -> List[Dict[str, Any]]:
        """Elabora un singolo file dall'estrazione all'arricchimento del chunk."""
        logger.info(f"Avvio elaborazione per il file: {path.name}")
        document_id = str(path.name)
        raw_text = self.text_extractor.extract(
            path,
            self.config.MIN_EXTRACTED_TEXT_SIZE,
            self.config.TABLE_PREVIEW_ROWS
        )
        if not raw_text:
            self._quarantine_file(path, "Estrazione del testo fallita o contenuto del file vuoto dopo lo strip.")
            return []

        text_for_classification = raw_text[:self.config.FULL_TEXT_CLASSIFICATION_LIMIT]
        llm_response = call_llm_for_classification(
            text_for_classification,
            path.name,
            self.config.SEMANTIC_CATEGORIES,
            "deepseek-r1:14b" 
        )
        category = llm_response.get("category", "unclassified")
        confidence = llm_response.get("confidence", 0.0)

        review_reason = None
        if not category or category == "unclassified":
            review_reason = f"LLM non è riuscito a classificare o ha restituito 'unclassified'. Confidenza: {confidence:.2f}"
            self._quarantine_file(path, review_reason)
            return []

        logger.info(f"Classificazione iniziale per '{path.name}': {category} (Confidenza: {confidence:.2f})")

        # Cross-check per confidenza più bassa o per categorie critiche
        if confidence < self.config.CROSS_CHECK_CONFIDENCE_THRESHOLD: 
            logger.info(f"Confidenza per '{path.name}' è inferiore alla soglia ({confidence:.2f} < {self.config.CROSS_CHECK_CONFIDENCE_THRESHOLD}). Eseguo cross-check...")
            cross_check_response = call_llm_for_classification(
                text_for_classification,
                path.name,
                self.config.SEMANTIC_CATEGORIES,
                "mistral" 
            )
            cross_check_category = cross_check_response.get("category")
            if not cross_check_category or cross_check_category != category:
                review_reason = f"Discrepanza di classificazione. Primaria ({llm_client.default_model}): {category} (Conf: {confidence:.2f}), Secondaria (Mistral): {cross_check_category} (Conf: {cross_check_response.get('confidence',0.0):.2f})."
                self._quarantine_file(path, review_reason)
                return []
            else:
                logger.info(f"Cross-check per '{path.name}' completato con successo. Modelli primario e secondario concordano.")
        
        entities = self.entity_extractor.extract(raw_text)
        
        # Determina lo stato del prodotto (per categoria 'product_price')
        product_status = "active"
        if category == "product_price" and "discontinued" in path.name.lower(): 
            product_status = "discontinued"
        
        file_stat = path.stat()
        base_metadata = {
            "source_filename": path.name,
            "relative_path": str(path.parent.relative_to(Path.cwd())) if Path.cwd() in path.parents else str(path.parent), 
            "category": category,
            "classification_confidence": f"{confidence:.2f}",
            "classifier": "llm_semantic_with_cross_check",
            "processed_at": pd.Timestamp.utcnow().isoformat(),
            "file_creation_time": pd.Timestamp.fromtimestamp(file_stat.st_ctime).isoformat(),
            "file_modification_time": pd.Timestamp.fromtimestamp(file_stat.st_mtime).isoformat(),
            "file_size_bytes": file_stat.st_size,
            "document_entities": entities,
            "requires_manual_review": review_reason is not None,
            "review_reason": review_reason
        }
        base_metadata[self.config.PRODUCT_STATUS_FIELD_NAME] = product_status

        chunker = self.chunker_map.get(category, self.chunker_map["default"])
        
        content_for_chunking = path if isinstance(chunker, StructuredDataExtractor) else raw_text
        chunks = chunker.chunk(content_for_chunking, document_id, base_metadata)

        enriched_chunks = []
        for chunk in chunks:
            # Salta l'arricchimento per contenuto vuoto o se è già una stringa JSON strutturata
            if not chunk.get('content') or chunk['content'].strip() == "{}" or chunk['content'].strip() == "[]":
                logger.warning(f"Salto l'arricchimento per chunk vuoto/strutturato/JSON: {chunk.get('chunk_id', 'N/A')}")
                enriched_chunks.append(chunk)
                continue

            # Controlla se il contenuto è già un oggetto JSON (da StructuredDataExtractor)
            is_json_content = False
            content_obj = None
            try:
                content_obj = json.loads(chunk['content'])
                if isinstance(content_obj, dict): # Assicurati che sia un oggetto, non una lista o altro
                    is_json_content = True
            except json.JSONDecodeError:
                pass 

            if is_json_content:
                # Se il contenuto è già JSON, estrai riassunto e domande dai suoi campi
                summary_parts = []
                # Migliorata la costruzione del riassunto per i chunk strutturati
                if 'description' in content_obj and content_obj['description']:
                    summary_parts.append(content_obj['description'])
                if 'serial' in content_obj and content_obj['serial']:
                    summary_parts.append(f"Seriale: {content_obj['serial']}")
                if 'price' in content_obj and content_obj['price'] is not None:
                    summary_parts.append(f"Prezzo: {content_obj['price']:.2f}€")
                if 'sheet_name' in content_obj and content_obj['sheet_name']:
                    summary_parts.append(f"Foglio: {content_obj['sheet_name']}")
                if PipelineConfig.PRODUCT_STATUS_FIELD_NAME in content_obj and content_obj[PipelineConfig.PRODUCT_STATUS_FIELD_NAME] == "discontinued":
                    summary_parts.append("Stato: Discontinuato")

                chunk['metadata']['chunk_summary'] = ", ".join(summary_parts) if summary_parts else "Nessun riassunto disponibile."
                
                # Generazione dinamica di domande ipotetiche per chunk strutturati
                chunk['metadata']['hypothetical_questions'] = []
                if 'description' in content_obj and content_obj['description']:
                    chunk['metadata']['hypothetical_questions'].append(f"Qual è il prezzo di {content_obj['description']}?")
                    chunk['metadata']['hypothetical_questions'].append(f"Qual è il seriale di {content_obj['description']}?")
                elif 'serial' in content_obj and content_obj['serial']:
                    chunk['metadata']['hypothetical_questions'].append(f"Qual è la descrizione del prodotto con seriale {content_obj['serial']}?")
                    chunk['metadata']['hypothetical_questions'].append(f"Quanto costa il prodotto {content_obj['serial']}?")
                
                if 'sheet_name' in content_obj and content_obj['sheet_name']:
                    chunk['metadata']['hypothetical_questions'].append(f"A quale foglio appartiene {content_obj.get('description', content_obj.get('serial', 'questo prodotto'))}?")
                
                if PipelineConfig.PRODUCT_STATUS_FIELD_NAME in content_obj and content_obj[PipelineConfig.PRODUCT_STATUS_FIELD_NAME] == "discontinued":
                     chunk['metadata']['hypothetical_questions'].append(f"È {content_obj.get('description', content_obj.get('serial', 'questo prodotto'))} discontinuato?")
                     chunk['metadata']['hypothetical_questions'].append(f"Ci sono alternative per {content_obj.get('description', content_obj.get('serial', 'questo prodotto'))}?")


                enriched_chunks.append(chunk)
                continue # Salta la chiamata LLM per l'arricchimento

            # Se non è contenuto JSON, procedi con l'arricchimento LLM
            enrichment_data = call_llm_for_enrichment(chunk['content'])
            
            if isinstance(enrichment_data, dict):
                chunk_summary = enrichment_data.get("chunk_summary", "Nessun riassunto fornito dall'LLM.")
                hypothetical_questions = enrichment_data.get("hypothetical_questions", [])
                
                chunk['metadata']['chunk_summary'] = chunk_summary
                chunk['metadata']['hypothetical_questions'] = hypothetical_questions
            else:
                logger.warning(
                    f"[⚠️ Arricchimento saltato] L'LLM ha restituito un tipo inatteso per l'arricchimento del chunk '{chunk.get('chunk_id', '<sconosciuto>')}'. "
                    f"Atteso dict, ricevuto {type(enrichment_data)}. Contenuto raw: {repr(enrichment_data)[:300]}"
                )
                chunk['metadata']['chunk_summary'] = chunk['content'][:200] + "..." 
                chunk['metadata']['hypothetical_questions'] = [] 

            enriched_chunks.append(chunk)

        logger.info(f"Creati e arricchiti con successo {len(enriched_chunks)} chunk per '{path.name}'.")
        return enriched_chunks

    def run(self, input_path: Path) -> List[Dict[str, Any]]:
        """Scansiona ed elabora i file in parallelo."""
        all_chunks = []
        files = self.scanner.scan(input_path)
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_file = {executor.submit(self.process_file, file): file for file in files}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result_chunks = future.result()
                    if result_chunks: 
                        all_chunks.extend(result_chunks)
                except Exception as e:
                    logger.critical(f"Errore critico durante l'elaborazione di '{file.name}': {e}", exc_info=True)
                    self._quarantine_file(file, f"Errore critico della pipeline: {e}")

        self.scanner.cleanup()
        logger.info(f"Pipeline completata. Totale chunk generati: {len(all_chunks)}")
        return all_chunks

# --- 7. ESECUZIONE DA LINEA DI COMANDO ---
def main():
    parser = argparse.ArgumentParser(description="Pipeline di Ingestione della Conoscenza Parallela e Focalizzata sull'Affidabilità.")
    parser.add_argument("input_path", type=str, help="Percorso della directory o del file ZIP con i documenti.")
    parser.add_argument("--output", default="knowledge_base_reliable.jsonl", help="File di output in formato JSON Lines.")
    args = parser.parse_args()

    config = PipelineConfig()
    pipeline = KnowledgePipeline(config)
    processed_chunks = pipeline.run(Path(args.input_path))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in processed_chunks:
            # Uso json.dumps con ensure_ascii=False per la corretta gestione dei caratteri non ASCII
            # e indent=None per una singola riga JSON (più efficiente per grandi file)
            f.write(json.dumps(chunk, ensure_ascii=False, indent=None) + '\n') 
    logger.info(f"Risultati salvati in: {output_path}")
    logger.info(f"I file che richiedono revisione manuale sono stati spostati nella directory '{config.QUARANTINE_DIR}'.")

if __name__ == "__main__":
    main()
