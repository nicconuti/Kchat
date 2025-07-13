#!/usr/bin/env python3
"""
PDF User Guide Retrieval System for K-Array Products
Versione migliorata: input da file "product_links.txt", scraping adattivo, salvataggio strutturato
"""

import os
import re
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import hashlib

# PDF Processing
try:
    import fitz  # PyMuPDF
    PDF_LIBRARY = "PyMuPDF"
except ImportError:
    PDF_LIBRARY = None

# Web Scraping con JS support
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class PDFUserGuideRetriever:
    def __init__(self,
                 product_links_file: str = "product_links.txt",
                 output_dir: str = "data/user_guides",
                 delay: float = 2.0):

        self.product_links_file = Path(product_links_file)
        self.output_dir = Path(output_dir)
        self.delay = delay

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()

        self.user_guide_patterns = [
            r'user\s+guide', r'user\s+manual', r'operation\s+manual',
            r'instruction\s+manual', r'operating\s+instructions',
            r'guida\s+utente', r'manuale\s+utente', r'manual\s+de\s+usuario',
            r'guide\s+utilisateur']

        self.stats = {
            'products_processed': 0,
            'pdf_links_found': 0,
            'user_guides_downloaded': 0,
            'errors': 0
        }

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pdf_retrieval.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_product_urls_from_file(self) -> List[str]:
        """Carica e normalizza gli URL dal file"""
        if not self.product_links_file.exists():
            self.logger.error(f"File non trovato: {self.product_links_file}")
            return []

        urls = set()
        with self.product_links_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                line = re.sub(r'^#?ttps?', 'https', line)
                if "/en/product/" in line:
                    urls.add(line)

        return sorted(urls)

    def extract_pdf_links_playwright(self, url: str) -> List[str]:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0"})
                page.goto(url, timeout=30000)
                page.wait_for_timeout(3000)

                links = page.query_selector_all('a[href*="download-file"], a[href$=".pdf"]')
                pdf_links = [urljoin(url, l.get_attribute("href")) for l in links if l.get_attribute("href")]
                browser.close()
                return list(set(pdf_links))
        except Exception as e:
            self.logger.error(f"Errore Playwright su {url}: {e}")
            return []

    def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(pdf_url, headers=headers, timeout=30)
            r.raise_for_status()
            if b"%PDF" in r.content[:1024]:
                return r.content
            return None
        except Exception as e:
            self.logger.error(f"Errore download PDF: {pdf_url}: {e}")
            return None

    def is_user_guide(self, pdf_content: bytes) -> bool:
        if PDF_LIBRARY != "PyMuPDF":
            return False
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            text = " ".join([doc[i].get_text().lower() for i in range(min(3, len(doc)))])
            doc.close()
            return any(re.search(p, text) for p in self.user_guide_patterns)
        except Exception as e:
            self.logger.warning(f"Errore lettura PDF: {e}")
            return False

    def save_user_guide(self, pdf_content: bytes, product_name: str, index: int) -> None:
        filename = f"{product_name}_guide_{index}.pdf"
        filepath = self.output_dir / filename
        with open(filepath, 'wb') as f:
            f.write(pdf_content)
        self.logger.info(f"Salvato: {filepath}")

    def get_product_name(self, url: str) -> str:
        return url.strip('/').split('/')[-1].replace('%20', '_')

    def process_product(self, url: str) -> None:
        product = self.get_product_name(url)
        self.logger.info(f"\nProcessing: {product}")
        try:
            pdf_links = self.extract_pdf_links_playwright(url)
            self.stats['pdf_links_found'] += len(pdf_links)
            found = 0
            for i, link in enumerate(pdf_links):
                content = self.download_pdf(link)
                if content and self.is_user_guide(content):
                    self.save_user_guide(content, product, i+1)
                    found += 1
                    self.stats['user_guides_downloaded'] += 1
                time.sleep(self.delay)
            self.logger.info(f"User guides trovate: {found}")
        except Exception as e:
            self.logger.error(f"Errore generale: {e}")
            self.stats['errors'] += 1

    def run(self):
        urls = self.load_product_urls_from_file()
        for url in urls:
            self.process_product(url)
            self.stats['products_processed'] += 1
        self.print_summary()

    def print_summary(self):
        self.logger.info("\n==== SUMMARY ====")
        for k, v in self.stats.items():
            self.logger.info(f"{k}: {v}")


def main():
    print("K-Array User Guide Retriever")
    retriever = PDFUserGuideRetriever()
    retriever.run()


if __name__ == "__main__":
    main()