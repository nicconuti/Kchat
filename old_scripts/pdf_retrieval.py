#!/usr/bin/env python3
"""
PDF User Guide Retrieval System for K-Array Products
Extracts user guide PDFs from product pages using JavaScript rendering
Compatible with Windows and handles dynamic content
"""

import os
import re
import time
import logging
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import hashlib

# PDF Processing
try:
    import fitz  # PyMuPDF
    PDF_LIBRARY = "PyMuPDF"
except ImportError:
    try:
        import pdfplumber
        PDF_LIBRARY = "pdfplumber"
    except ImportError:
        try:
            import PyPDF2
            PDF_LIBRARY = "PyPDF2"
        except ImportError:
            PDF_LIBRARY = None

# Web Scraping with JS support
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from requests_html import HTMLSession
    REQUESTS_HTML_AVAILABLE = True
except ImportError:
    REQUESTS_HTML_AVAILABLE = False


class PDFUserGuideRetriever:
    """Advanced PDF User Guide retrieval system"""
    
    def __init__(self, 
                 base_url: str = "https://www.k-array.com",
                 output_dir: str = "data/user_guides",
                 delay: float = 2.0):
        
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.delay = delay
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # User guide detection patterns
        self.user_guide_patterns = [
            r'user\s+guide',
            r'user\s+manual',
            r'operation\s+manual',
            r'instruction\s+manual',
            r'operating\s+instructions',
            r'guida\s+utente',
            r'manuale\s+utente',
            r'manual\s+de\s+usuario',
            r'guide\s+utilisateur'
        ]
        
        # Statistics
        self.stats = {
            'products_processed': 0,
            'pdf_links_found': 0,
            'user_guides_downloaded': 0,
            'errors': 0,
            'skipped': 0
        }
        
        # Select best available scraping method
        self.scraping_method = self.select_scraping_method()
        self.logger.info(f"Using scraping method: {self.scraping_method}")
        self.logger.info(f"Using PDF library: {PDF_LIBRARY}")
    
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pdf_retrieval.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def select_scraping_method(self) -> str:
        """Select the best available scraping method"""
        if PLAYWRIGHT_AVAILABLE:
            return "playwright"
        elif SELENIUM_AVAILABLE:
            return "selenium"
        elif REQUESTS_HTML_AVAILABLE:
            return "requests_html"
        else:
            return "requests_only"
    
    def load_product_urls_from_sitemap(self, sitemap_path: str = "sitemap.xml") -> List[str]:
        """Load product URLs from sitemap.xml"""
        try:
            if not Path(sitemap_path).exists():
                self.logger.error(f"Sitemap not found: {sitemap_path}")
                return []
            
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            
            # Extract product URLs
            product_urls = []
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc_elem is not None:
                    url = loc_elem.text
                    if '/en/product/' in url:
                        product_urls.append(url)
            
            self.logger.info(f"Loaded {len(product_urls)} product URLs from sitemap")
            return product_urls
            
        except Exception as e:
            self.logger.error(f"Error loading sitemap: {e}")
            return []
    
    def extract_pdf_links_playwright(self, url: str) -> List[str]:
        """Extract PDF links using Playwright"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set user agent and timeout
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                
                # Navigate to page
                page.goto(url, timeout=30000)
                
                # Wait for page to load and JS to execute
                page.wait_for_timeout(3000)
                
                # Look for download links
                pdf_links = []
                
                # Strategy 1: Look for direct PDF links
                links = page.query_selector_all('a[href*="download-file"], a[href$=".pdf"]')
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        pdf_links.append(urljoin(url, href))
                
                # Strategy 2: Look in Downloads section
                download_sections = page.query_selector_all('div:has-text("Downloads"), section:has-text("Downloads")')
                for section in download_sections:
                    links = section.query_selector_all('a')
                    for link in links:
                        href = link.get_attribute('href')
                        text = link.text_content() or ""
                        if href and ("download" in href.lower() or "guide" in text.lower() or "manual" in text.lower()):
                            pdf_links.append(urljoin(url, href))
                
                # Strategy 3: Look for any links containing "guide" or "manual"
                guide_links = page.query_selector_all('a:has-text("guide"), a:has-text("Guide"), a:has-text("manual"), a:has-text("Manual")')
                for link in guide_links:
                    href = link.get_attribute('href')
                    if href:
                        pdf_links.append(urljoin(url, href))
                
                browser.close()
                
                # Remove duplicates
                pdf_links = list(set(pdf_links))
                self.logger.info(f"Found {len(pdf_links)} PDF links on {url}")
                
                return pdf_links
                
        except Exception as e:
            self.logger.error(f"Error extracting PDF links with Playwright from {url}: {e}")
            return []
    
    def extract_pdf_links_selenium(self, url: str) -> List[str]:
        """Extract PDF links using Selenium"""
        try:
            # Setup Chrome options
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            try:
                # Navigate to page
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Additional wait for dynamic content
                time.sleep(3)
                
                pdf_links = []
                
                # Find all links
                links = driver.find_elements(By.TAG_NAME, "a")
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        text = link.text.lower()
                        
                        if href and (
                            'download-file' in href or
                            href.endswith('.pdf') or
                            'guide' in text or
                            'manual' in text
                        ):
                            pdf_links.append(href)
                    except:
                        continue
                
                # Remove duplicates
                pdf_links = list(set(pdf_links))
                self.logger.info(f"Found {len(pdf_links)} PDF links on {url}")
                
                return pdf_links
                
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error extracting PDF links with Selenium from {url}: {e}")
            return []
    
    def extract_pdf_links_requests_html(self, url: str) -> List[str]:
        """Extract PDF links using requests-html"""
        try:
            session = HTMLSession()
            
            # Get page
            r = session.get(url, timeout=30)
            
            # Render JavaScript
            r.html.render(timeout=20, sleep=3)
            
            pdf_links = []
            
            # Find PDF links
            for link in r.html.absolute_links:
                if ('download-file' in link or 
                    link.endswith('.pdf') or
                    'guide' in link.lower() or
                    'manual' in link.lower()):
                    pdf_links.append(link)
            
            # Also check link text
            for element in r.html.find('a'):
                text = element.text.lower() if element.text else ""
                href = element.attrs.get('href', '')
                
                if ('guide' in text or 'manual' in text) and href:
                    full_url = urljoin(url, href)
                    pdf_links.append(full_url)
            
            session.close()
            
            # Remove duplicates
            pdf_links = list(set(pdf_links))
            self.logger.info(f"Found {len(pdf_links)} PDF links on {url}")
            
            return pdf_links
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF links with requests-html from {url}: {e}")
            return []
    
    def extract_pdf_links_basic(self, url: str) -> List[str]:
        """Basic extraction without JavaScript (fallback)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text
            pdf_links = []
            
            # Simple regex patterns for PDF links
            patterns = [
                r'href="([^"]*download-file[^"]*)"',
                r'href="([^"]*\.pdf)"',
                r'href="([^"]*)"[^>]*>.*?(?:guide|manual)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    full_url = urljoin(url, match)
                    pdf_links.append(full_url)
            
            # Remove duplicates
            pdf_links = list(set(pdf_links))
            self.logger.info(f"Found {len(pdf_links)} PDF links on {url} (basic method)")
            
            return pdf_links
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF links with basic method from {url}: {e}")
            return []
    
    def extract_pdf_links(self, url: str) -> List[str]:
        """Extract PDF links using the best available method"""
        self.logger.info(f"Extracting PDF links from: {url}")
        
        if self.scraping_method == "playwright":
            return self.extract_pdf_links_playwright(url)
        elif self.scraping_method == "selenium":
            return self.extract_pdf_links_selenium(url)
        elif self.scraping_method == "requests_html":
            return self.extract_pdf_links_requests_html(url)
        else:
            return self.extract_pdf_links_basic(url)
    
    def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """Download PDF content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not pdf_url.endswith('.pdf'):
                # Check magic bytes
                if not response.content.startswith(b'%PDF'):
                    self.logger.warning(f"Not a PDF file: {pdf_url}")
                    return None
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            return None
    
    def is_user_guide(self, pdf_content: bytes) -> Tuple[bool, str]:
        """Check if PDF is a user guide and extract title"""
        try:
            text_content = ""
            title = ""
            
            if PDF_LIBRARY == "PyMuPDF":
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                
                # Extract title from metadata
                metadata = doc.metadata
                if metadata.get('title'):
                    title = metadata['title']
                
                # Extract text from first few pages
                for page_num in range(min(3, len(doc))):
                    page = doc[page_num]
                    text_content += page.get_text().lower()
                
                doc.close()
                
            elif PDF_LIBRARY == "pdfplumber":
                import io
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    # Extract text from first few pages
                    for page_num in range(min(3, len(pdf.pages))):
                        page = pdf.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text.lower()
                            
                            # Try to extract title from first page
                            if page_num == 0 and not title:
                                lines = page_text.split('\n')
                                for line in lines[:10]:  # Check first 10 lines
                                    line = line.strip()
                                    if len(line) > 5 and any(word in line.lower() for word in ['guide', 'manual']):
                                        title = line
                                        break
            
            elif PDF_LIBRARY == "PyPDF2":
                import io
                from PyPDF2 import PdfReader
                
                reader = PdfReader(io.BytesIO(pdf_content))
                
                # Extract metadata title
                if reader.metadata and reader.metadata.title:
                    title = reader.metadata.title
                
                # Extract text from first few pages
                for page_num in range(min(3, len(reader.pages))):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text.lower()
            
            # Check for user guide patterns
            for pattern in self.user_guide_patterns:
                if re.search(pattern, text_content, re.IGNORECASE):
                    self.logger.info(f"User guide detected with pattern: {pattern}")
                    return True, title
            
            return False, title
            
        except Exception as e:
            self.logger.error(f"Error analyzing PDF content: {e}")
            return False, ""
    
    def get_product_name_from_url(self, url: str) -> str:
        """Extract product name from URL"""
        try:
            # Extract from URL path
            path = urlparse(url).path
            product_name = path.split('/')[-1]
            
            # Clean up the name
            product_name = re.sub(r'[^\w\-]', '', product_name)
            
            return product_name
            
        except Exception as e:
            self.logger.error(f"Error extracting product name from {url}: {e}")
            return "unknown_product"
    
    def save_user_guide(self, pdf_content: bytes, product_name: str, title: str = "") -> str:
        """Save user guide PDF with proper naming"""
        try:
            # Create filename
            if title and len(title) > 5:
                # Use title if available
                clean_title = re.sub(r'[^\w\s\-]', '', title)
                clean_title = re.sub(r'\s+', '_', clean_title.strip())
                filename = f"{product_name}_{clean_title}.pdf"
            else:
                filename = f"{product_name}_user_guide.pdf"
            
            # Ensure filename is not too long
            if len(filename) > 100:
                filename = f"{product_name}_user_guide.pdf"
            
            filepath = self.output_dir / filename
            
            # Avoid duplicates
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                stem = original_filepath.stem
                suffix = original_filepath.suffix
                filepath = original_filepath.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            
            self.logger.info(f"Saved user guide: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving user guide for {product_name}: {e}")
            return ""
    
    def process_product(self, product_url: str) -> Dict:
        """Process a single product page"""
        result = {
            'url': product_url,
            'product_name': '',
            'pdf_links_found': 0,
            'user_guides_downloaded': 0,
            'success': False,
            'error': None
        }
        
        try:
            # Extract product name
            product_name = self.get_product_name_from_url(product_url)
            result['product_name'] = product_name
            
            self.logger.info(f"Processing product: {product_name} ({product_url})")
            
            # Extract PDF links
            pdf_links = self.extract_pdf_links(product_url)
            result['pdf_links_found'] = len(pdf_links)
            self.stats['pdf_links_found'] += len(pdf_links)
            
            if not pdf_links:
                self.logger.info(f"No PDF links found for {product_name}")
                result['success'] = True  # Not an error, just no PDFs
                return result
            
            # Process each PDF link
            for pdf_url in pdf_links:
                self.logger.info(f"Checking PDF: {pdf_url}")
                
                # Download PDF
                pdf_content = self.download_pdf(pdf_url)
                if not pdf_content:
                    continue
                
                # Check if it's a user guide
                is_guide, title = self.is_user_guide(pdf_content)
                
                if is_guide:
                    # Save the user guide
                    saved_path = self.save_user_guide(pdf_content, product_name, title)
                    if saved_path:
                        result['user_guides_downloaded'] += 1
                        self.stats['user_guides_downloaded'] += 1
                        self.logger.info(f"✅ User guide saved for {product_name}")
                else:
                    self.logger.info(f"PDF is not a user guide: {pdf_url}")
                
                # Rate limiting
                time.sleep(self.delay)
            
            result['success'] = True
            
        except Exception as e:
            error_msg = f"Error processing {product_url}: {e}"
            self.logger.error(error_msg)
            result['error'] = str(e)
            self.stats['errors'] += 1
        
        return result
    
    def run(self, max_products: Optional[int] = None) -> Dict:
        """Run the PDF user guide retrieval process"""
        
        self.logger.info("🔍 Starting PDF User Guide Retrieval")
        self.logger.info("=" * 60)
        
        # Check dependencies
        if not PDF_LIBRARY:
            self.logger.error("❌ No PDF processing library available!")
            self.logger.error("Install one of: pip install PyMuPDF pdfplumber PyPDF2")
            return self.stats
        
        if self.scraping_method == "requests_only":
            self.logger.warning("⚠️ Using basic scraping without JavaScript support")
            self.logger.warning("For better results, install: pip install playwright selenium requests-html")
        
        # Load product URLs
        product_urls = self.load_product_urls_from_sitemap()
        
        if not product_urls:
            self.logger.error("❌ No product URLs found!")
            return self.stats
        
        # Limit products if specified
        if max_products:
            product_urls = product_urls[:max_products]
            self.logger.info(f"📊 Processing first {max_products} products (limited)")
        
        self.logger.info(f"📊 Found {len(product_urls)} products to process")
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        
        # Process each product
        for i, product_url in enumerate(product_urls, 1):
            self.logger.info(f"\n[{i}/{len(product_urls)}] Processing product...")
            
            result = self.process_product(product_url)
            self.stats['products_processed'] += 1
            
            # Progress update
            if i % 10 == 0:
                self.logger.info(f"Progress: {i}/{len(product_urls)} products processed")
                self.logger.info(f"User guides found: {self.stats['user_guides_downloaded']}")
        
        return self.stats
    
    def print_summary(self):
        """Print final summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 PDF RETRIEVAL SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"📄 Products processed: {self.stats['products_processed']}")
        self.logger.info(f"🔗 PDF links found: {self.stats['pdf_links_found']}")
        self.logger.info(f"📚 User guides downloaded: {self.stats['user_guides_downloaded']}")
        self.logger.info(f"❌ Errors: {self.stats['errors']}")
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        
        if self.stats['user_guides_downloaded'] > 0:
            self.logger.info(f"\n🎉 SUCCESS! Downloaded {self.stats['user_guides_downloaded']} user guides!")
            self.logger.info(f"💡 Next step: Integrate PDFs with vector store using:")
            self.logger.info(f"   python3 integrate_pdf_content.py")
        else:
            self.logger.info(f"\n⚠️ No user guides found. Check:")
            self.logger.info(f"   - PDF detection patterns")
            self.logger.info(f"   - JavaScript rendering capability")
            self.logger.info(f"   - Network connectivity")


def main():
    """Main function"""
    
    print("🔍 PDF User Guide Retrieval System for K-Array Products")
    print("=" * 60)
    
    # Check available libraries
    print(f"📚 PDF Library: {PDF_LIBRARY or 'None available'}")
    print(f"🌐 Scraping: Playwright={PLAYWRIGHT_AVAILABLE}, Selenium={SELENIUM_AVAILABLE}, requests-html={REQUESTS_HTML_AVAILABLE}")
    
    if not PDF_LIBRARY:
        print("\n❌ No PDF processing library found!")
        print("Install one of:")
        print("   pip install PyMuPDF          # Recommended")
        print("   pip install pdfplumber       # Alternative")
        print("   pip install PyPDF2           # Basic")
        return
    
    # Create retriever
    retriever = PDFUserGuideRetriever()
    
    # Run with limit for testing (remove limit for full run)
    print(f"\n🚀 Starting retrieval process...")
    print(f"⏱️ Rate limiting: {retriever.delay}s between requests")
    
    # For initial testing, limit to 5 products
    # For full run, remove max_products parameter
    stats = retriever.run(max_products=5)  # Remove this limit for full run
    
    # Print summary
    retriever.print_summary()


if __name__ == "__main__":
    main()