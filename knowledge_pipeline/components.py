import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional
import re

import docx
import pandas as pd
import fitz  # PyMuPDF
import spacy
from functools import lru_cache
from spacy.cli.download import download

from .logging_config import setup_logging

logger = setup_logging()


class FileScanner:
    """Scansiona ricorsivamente una directory, un singolo file o un file ZIP."""

    def __init__(self, extensions: set) -> None:
        self.supported_extensions = extensions
        self._temp_dir: Optional[TemporaryDirectory] = None

    def scan(self, path: Path) -> List[Path]:
        logger.info(f"Avvio scansione in: {path}")
        files_to_process: List[Path] = []
        if path.is_file():
            if path.suffix.lower() == ".zip":
                self._temp_dir = TemporaryDirectory()
                zip_base_path = Path(self._temp_dir.name)
                logger.info(f"Estrazione file ZIP in directory temporanea: {zip_base_path}")
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(zip_base_path)
                files_to_process = list(zip_base_path.rglob("*"))
            elif path.suffix.lower() in self.supported_extensions:
                files_to_process = [path]
            else:
                logger.warning(
                    f"Il singolo file '{path.name}' ha un'estensione non supportata '{path.suffix.lower()}'."
                )
                return []
        elif path.is_dir():
            files_to_process = list(path.rglob("*"))
        else:
            logger.error(f"Il percorso di input '{path}' non è valido")
            return []

        supported_files = [f for f in files_to_process if f.is_file() and f.suffix.lower() in self.supported_extensions]
        logger.info(f"Trovati {len(supported_files)} file supportati.")
        return supported_files

    def cleanup(self) -> None:
        if self._temp_dir:
            logger.info(f"Pulizia directory temporanea: {self._temp_dir.name}")
            self._temp_dir.cleanup()


class TextExtractor:
    """Estrae testo raw da vari formati di file."""

    def extract(self, path: Path, min_size: int, preview_rows: int) -> str:
        logger.info(f"Estrazione testo da: {path.name}")
        text = ""
        try:
            ext = path.suffix.lower()
            if ext == ".pdf":
                with fitz.open(path) as pdf:
                    all_text = [page.extract_text() for page in pdf.pages if page.extract_text()]
                text = "\n".join(all_text)
            elif ext == ".docx":
                doc = docx.Document(str(path))
                all_text = [para.text for para in doc.paragraphs if para.text.strip()]
                text = "\n".join(all_text)
            elif ext == ".xlsx":
                with pd.ExcelFile(path) as xls:
                    all_sheet_previews = []
                    for sheet_name in xls.sheet_names:
                        try:
                            df = pd.read_excel(xls, sheet_name=sheet_name, nrows=preview_rows)
                            all_sheet_previews.append(
                                f"--- Foglio: {sheet_name} ---\n{df.to_string(index=False)}"
                            )
                        except Exception as e:  # pragma: no cover - log and continue
                            logger.warning(f"Impossibile parsare il foglio '{sheet_name}' da '{path.name}': {e}")
                    text = "\n\n".join(all_sheet_previews)
            elif ext == ".csv":
                df = pd.read_csv(path, nrows=preview_rows)
                text = df.to_string(index=False)
            elif ext in [".json", ".xml", ".txt", ".html", ".htm"]:
                text = path.read_text(encoding="utf-8", errors="ignore")
            return "" if len(text.strip()) < min_size else text
        except Exception:  # pragma: no cover - log errors
            logger.error(f"Errore durante l'estrazione del testo da '{path.name}'.", exc_info=True)
            return ""


class EntityExtractor:
    """Estrae entità nominate dal testo usando SpaCy e filtra i termini generici."""

    @lru_cache(maxsize=1)
    def _get_nlp(self):
        logger.info("Caricamento del modello SpaCy 'xx_ent_wiki_sm'...")
        try:
            return spacy.load("xx_ent_wiki_sm")
        except OSError:  # pragma: no cover - attempt download
            logger.warning("Modello SpaCy 'xx_ent_wiki_sm' non trovato. Scarico...")
            download("xx_ent_wiki_sm")
            return spacy.load("xx_ent_wiki_sm")

    def extract(self, text: str) -> List[str]:
        nlp = self._get_nlp()
        doc = nlp(text)
        noisy_terms = {
            "nan",
            "price",
            "description",
            "serial",
            "module",
            "board",
            "amplifier",
            "watt",
            "inch",
            "ohm",
            "ch",
            "new",
            "empty",
            "full",
            "pcs",
            "model",
            "list",
            "total",
            "category",
            "number",
            "code",
            "part",
            "component",
            "interface",
            "panel",
            "rack",
            "logo",
            "i",
            "ii",
            "iii",
            "v",
            "l",
            "s",
            "to",
            "be",
            "used",
            "with",
            "from",
            "until",
            "for",
            "with",
            "a",
            "an",
            "the",
            "and",
        }
        entities = set()
        for ent in doc.ents:
            entity_text = ent.text.strip()
            if ent.label_ in {"ORG", "PRODUCT", "WORK_OF_ART", "MISC"} and len(entity_text) > 2 and entity_text.lower() not in noisy_terms:
                if not re.fullmatch(r"(\d+|\n|\s)+", entity_text):
                    entities.add(entity_text)
        logger.info(f"Estratti {len(entities)} entità uniche e filtrate.")
        return sorted(list(entities))
