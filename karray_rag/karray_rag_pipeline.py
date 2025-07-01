import logging
import hashlib
import json
from pathlib import Path
from typing import List, Tuple, Set, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import fitz  # PyMuPDF
import trafilatura
import argparse
from datetime import datetime
import re

from haystack import Document
from rag_store import save_documents_to_jsonl

logger = logging.getLogger("KArrayCrawler")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CACHE_PATH = Path("data/document_cache.json")

CATEGORY_PATTERNS = {
    "products": ["/products", "/product"],
    "applications": ["/applications"],
    "projects": ["/projects", "/case-studies"],
    "support": ["/support", "/downloads", "/manual", "/firmware"],
    "about": ["/about", "/company", "/history", "/values"],
    "news": ["/blog", "/news", "/post"],
    "contact": ["/contact", "/dealers", "/distributor"]
}

IGNORED_EXTENSIONS = (".zip", ".exe", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".js", ".css", ".mp3", ".mp4")
BLACKLISTED_PATHS = ["/es", "es/", "/newsletter", "/subscribe", "/cookie", "/privacy", "/terms"]


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip('/'),
        params='',
        query='',
        fragment=''
    )
    return normalized.geturl()


def categorize_url(url: str) -> str:
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(p in url for p in patterns):
            return category
    return "general_info"


def load_cache(path: Path) -> Dict[str, Dict]:
    if not path.exists():
        logger.info(f"Cache non trovata a {path}. Creazione di una nuova cache.")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            cache = json.load(f)
            logger.info(f"✅ Cache caricata da {path} con {len(cache)} voci.")
            return cache
    except json.JSONDecodeError:
        logger.error(f"❌ Cache corrotta o formato JSON non valido a {path}. Verrà ignorata.")
        return {}
    except Exception as e:
        logger.error(f"❌ Errore durante il caricamento della cache da {path}: {e}. Verrà ignorata.")
        return {}


def save_cache(cache: Dict[str, Dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Cache salvata a {path} con {len(cache)} voci.")
    except IOError as e:
        logger.error(f"❌ Errore I/O durante il salvataggio della cache a {path}: {e}")
    except Exception as e:
        logger.error(f"❌ Errore generico durante il salvataggio della cache: {e}")


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text_parts = [page.get_text("text") for page in doc]
        return "\n\n".join(text_parts).strip()
    except Exception as e:
        logger.error(f"❌ Errore estrazione testo da PDF: {e}")
        return ""


def clean_extracted_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text


def fetch_html_recursive(url: str, base_domain: str, max_depth: int = 5, visited_url: Set[str] = None, cache: Dict = None, force: bool = False) -> List[Tuple[str, str, str, str]]:
    if visited_url is None:
        visited_url = set()
    if cache is None:
        cache = {}

    normalized_url = normalize_url(url)
    if normalized_url in visited_url or max_depth < 0:
        logger.debug(f"⏭️ Skipping {url} (normalized: {normalized_url}): già visitato o profondità esaurita.")
        return []

    if any(p in normalized_url for p in BLACKLISTED_PATHS) or normalized_url.endswith(IGNORED_EXTENSIONS):
        logger.info(f"🚫 Skipping {normalized_url}: path o estensione nella blacklist")
        return []

    visited_url.add(normalized_url)
    results = []

    try:
        logger.info(f"🌐 Fetching: {url} (Depth: {max_depth})")
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=15, headers=headers)
        r.raise_for_status()

        content_type = r.headers.get("Content-Type", "").lower()
        if any(ext in content_type for ext in ["application/octet-stream", "application/x-msdownload"]):
            logger.info(f"🚫 Skippando {url}: tipo di contenuto forzatamente bloccato ({content_type})")
            return []

        content = ""
        if "application/pdf" in content_type:
            content = extract_text_from_pdf_bytes(r.content)
            logger.info(f"📄 PDF estratto da: {url}")
        elif "text/html" in content_type:
            content = trafilatura.extract(
                r.text,
                include_comments=False,
                include_tables=True,
                favor_precision=True,
                deduplicate=True,
            )
            logger.info(f"📄 HTML estratto da: {url}")
        else:
            logger.info(f"🚫 Skippando {url}: tipo di contenuto non supportato ({content_type})")
            BLACKLISTED_PATHS.append(url)
            return []

        cleaned_content = clean_extracted_text(content)

        if not cleaned_content or len(cleaned_content) < 100:
            logger.warning(f"⚠️ Contenuto vuoto o insufficiente (<100 char) da {url}. Lunghezza: {len(cleaned_content)}")
            return []

        content_hash = compute_sha256(cleaned_content)
        if not force and normalized_url in cache and cache[normalized_url]["sha256"] == content_hash:
            logger.info(f"⏩ {url}: Nessuna modifica rilevata, salto. (Hash: {content_hash[:8]})")
            return []

        cache[normalized_url] = {
            "sha256": content_hash,
            "last_processed": datetime.utcnow().isoformat(),
        }
        category = categorize_url(normalized_url)
        results.append((normalized_url, cleaned_content, content_type, category))

        if "text/html" in content_type:
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup.find_all('a', href=True):
                absolute_link = urljoin(url, tag['href'])
                parsed_link = urlparse(absolute_link)

                if parsed_link.netloc.endswith(base_domain) or parsed_link.netloc == base_domain:
                    clean_link = urljoin(absolute_link, parsed_link.path).rstrip('/')
                    normalized_link = normalize_url(clean_link)

                    if normalized_link.endswith(IGNORED_EXTENSIONS) or any(p in normalized_link for p in BLACKLISTED_PATHS):
                        logger.info(f"🚫 Skipping {normalized_link}: risorsa esclusa (estensione o path)")
                        continue

                    if normalized_link not in visited_url:
                        results.extend(fetch_html_recursive(normalized_link, base_domain, max_depth - 1, visited_url, cache, force))

    except requests.exceptions.RequestException as req_e:
        logger.warning(f"⚠️ Errore di richiesta HTTP per {url}: {req_e}")
    except Exception as e:
        logger.error(f"❌ Errore imprevisto durante il fetch da {url}: {e}")

    return results


def run_pipeline_with_karray(url: str = "https://www.k-array.com/", max_depth: int = 5, force: bool = False, cache_path: Path = CACHE_PATH):
    base_domain = urlparse(url).netloc.replace("www.", "")
    logger.info(f"\n Inizio crawling di {base_domain} da {url} (max_depth: {max_depth})...\n")

    cache = load_cache(cache_path)
    pages = fetch_html_recursive(url, base_domain=base_domain, max_depth=max_depth, cache=cache, force=force)

    if not pages:
        logger.info("Nessun nuovo documento da processare o nessun cambiamento rilevato.")
        save_cache(cache, cache_path)
        return

    documents: List[Document] = []
    for i, (doc_url, content, content_type, category) in enumerate(pages):
        doc = Document(
            content=content,
            meta={
                "source": doc_url,
                "content_type": "pdf" if "pdf" in content_type else "html",
                "category": category,
                "crawled_at": datetime.now().isoformat()
            }
        )
        documents.append(doc)

    output_path = Path("data/karray_knowledge.jsonl")
    save_documents_to_jsonl(documents, output_path)
    save_cache(cache, cache_path)

    logger.info(f"\n✅ Pipeline completata. Estratti {len(documents)} documenti. Output salvato in: {output_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl + RAG pipeline su k-array.com con caching e categorizzazione")
    parser.add_argument("--url", type=str, default="https://www.k-array.com/en", help="URL root da cui iniziare il crawl")
    parser.add_argument("--depth", type=int, default=5, help="Profondità massima del crawling")
    parser.add_argument("--force", action="store_true", help="Ignora la cache e forza il crawling completo")
    parser.add_argument("--cache-path", type=Path, default=CACHE_PATH, help="Percorso del file di cache JSON")
    args = parser.parse_args()

    run_pipeline_with_karray(url=args.url, max_depth=args.depth, force=args.force, cache_path=args.cache_path)