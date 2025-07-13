#!/usr/bin/env python3
"""
Comprehensive PDF Extractor for K-Array Products
Extracts all PDFs from sitemap.xml product pages with duplicate detection
"""

import os
import re
import time
import logging
import hashlib
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from collections import defaultdict

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
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class ComprehensivePDFExtractor:
    """Comprehensive PDF extractor for all K-Array products"""
    
    def __init__(self, 
                 base_url: str = "https://www.k-array.com",
                 output_dir: str = "data/user_guides",
                 sitemap_path: str = "sitemap.xml",
                 delay: float = 2.0):
        
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.sitemap_path = sitemap_path
        self.delay = delay
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Duplicate detection
        self.downloaded_pdfs = {}  # URL -> file_path
        self.pdf_hashes = set()    # Content hashes
        self.processed_urls = set()  # Processed product URLs
        
        # Statistics
        self.stats = {
            'total_product_urls': 0,
            'processed_product_urls': 0,
            'pdf_links_found': 0,
            'user_guides_downloaded': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'processing_time': 0
        }
        
        # Setup logging
        self.setup_logging()
        
        # User guide detection patterns
        self.user_guide_patterns = [
            r'user\s+guide',
            r'user\s+manual',
            r'operation\s+manual',
            r'instruction\s+manual',
            r'operating\s+instructions',
            r'installation\s+guide',
            r'quick\s+start',
            r'getting\s+started',
            r'setup\s+guide',
            r'guida\s+utente',
            r'manuale\s+utente',
            r'manual\s+de\s+usuario',
            r'guide\s+utilisateur'
        ]
    
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('comprehensive_pdf_extraction.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_all_product_urls_from_sitemap(self) -> List[str]:
        """Load ALL product URLs from sitemap.xml"""
        try:
            if not Path(self.sitemap_path).exists():
                self.logger.error(f"Sitemap not found: {self.sitemap_path}")
                return []
            
            self.logger.info(f"Loading product URLs from {self.sitemap_path}")
            
            tree = ET.parse(self.sitemap_path)
            root = tree.getroot()
            
            # Extract ALL product URLs
            product_urls = []
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc_elem is not None:
                    url = loc_elem.text
                    # Include ALL product URLs (not just /en/product/)
                    if '/en/product' in url or '/product' in url:
                        product_urls.append(url)
            
            # Remove duplicates and sort
            product_urls = sorted(list(set(product_urls)))
            
            self.logger.info(f"Found {len(product_urls)} unique product URLs")
            self.stats['total_product_urls'] = len(product_urls)
            
            return product_urls
            
        except Exception as e:
            self.logger.error(f"Error loading sitemap: {e}")
            return []
    
    def extract_pdf_links_with_playwright(self, url: str) -> List[str]:
        """Extract PDF links using Playwright with comprehensive search"""
        if not PLAYWRIGHT_AVAILABLE:
            return self.extract_pdf_links_with_requests(url)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set user agent
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                # Navigate with timeout
                page.goto(url, timeout=30000, wait_until='networkidle')
                
                # Wait for dynamic content
                page.wait_for_timeout(3000)
                
                pdf_links = set()
                
                # Strategy 1: Direct PDF links
                links = page.query_selector_all('a[href*=".pdf"], a[href*="download-file"], a[href*="download"]')
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        full_url = urljoin(url, href)
                        pdf_links.add(full_url)
                
                # Strategy 2: Downloads section
                download_sections = page.query_selector_all(
                    'div:has-text("Downloads"), div:has-text("Documentation"), '
                    'section:has-text("Downloads"), div:has-text("Manuals")'
                )
                for section in download_sections:
                    links = section.query_selector_all('a')
                    for link in links:
                        href = link.get_attribute('href')
                        text = link.text_content() or ""
                        if href and any(pattern in text.lower() for pattern in 
                                      ['guide', 'manual', 'download', 'pdf', 'documentation']):
                            full_url = urljoin(url, href)
                            pdf_links.add(full_url)
                
                # Strategy 3: Look for specific text patterns
                guide_links = page.query_selector_all(
                    'a:has-text("guide"), a:has-text("Guide"), a:has-text("manual"), '
                    'a:has-text("Manual"), a:has-text("PDF"), a:has-text("Download")'
                )
                for link in guide_links:
                    href = link.get_attribute('href')
                    if href:
                        full_url = urljoin(url, href)
                        pdf_links.add(full_url)
                
                # Strategy 4: Scan all links for PDF-like patterns
                all_links = page.query_selector_all('a[href]')
                for link in all_links:
                    href = link.get_attribute('href')
                    text = link.text_content() or ""
                    
                    if href and (
                        href.endswith('.pdf') or
                        'download-file' in href or
                        'manual' in href.lower() or
                        'guide' in href.lower() or
                        any(pattern.replace(r'\s+', ' ') in text.lower() 
                            for pattern in self.user_guide_patterns)
                    ):
                        full_url = urljoin(url, href)
                        pdf_links.add(full_url)
                
                browser.close()
                
                pdf_links_list = list(pdf_links)
                self.logger.info(f"Found {len(pdf_links_list)} potential PDF links on {url}")
                
                return pdf_links_list
                
        except Exception as e:
            self.logger.error(f"Error extracting PDF links with Playwright from {url}: {e}")
            return self.extract_pdf_links_with_requests(url)
    
    def extract_pdf_links_with_requests(self, url: str) -> List[str]:
        """Fallback PDF extraction using requests + BeautifulSoup"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            pdf_links = set()
            
            if BS4_AVAILABLE:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    text = link.get_text(strip=True).lower()
                    
                    if (href.endswith('.pdf') or
                        'download-file' in href or
                        'manual' in href.lower() or
                        'guide' in href.lower() or
                        any(pattern.replace(r'\s+', ' ') in text 
                            for pattern in self.user_guide_patterns)):
                        
                        full_url = urljoin(url, href)
                        pdf_links.add(full_url)
            else:
                # Simple regex fallback
                href_pattern = r'href=["\']([^"\']*(?:\.pdf|download-file|manual|guide)[^"\']*)["\']'
                matches = re.findall(href_pattern, response.text, re.IGNORECASE)
                
                for match in matches:
                    full_url = urljoin(url, match)
                    pdf_links.add(full_url)
            
            pdf_links_list = list(pdf_links)
            self.logger.info(f"Found {len(pdf_links_list)} PDF links on {url} (fallback method)")
            
            return pdf_links_list
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF links with requests from {url}: {e}")
            return []
    
    def get_pdf_hash(self, pdf_content: bytes) -> str:
        """Generate hash for PDF content to detect duplicates"""
        return hashlib.md5(pdf_content).hexdigest()
    
    def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """Download PDF with duplicate detection"""
        try:
            # Check if URL already processed
            if pdf_url in self.downloaded_pdfs:
                self.logger.info(f"PDF URL already processed: {pdf_url}")
                self.stats['duplicates_skipped'] += 1
                return None
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Verify it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not pdf_url.endswith('.pdf'):
                if not response.content.startswith(b'%PDF'):
                    self.logger.warning(f"Not a PDF file: {pdf_url}")
                    return None
            
            # Check for duplicate content
            pdf_hash = self.get_pdf_hash(response.content)
            if pdf_hash in self.pdf_hashes:
                self.logger.info(f"Duplicate PDF content detected: {pdf_url}")
                self.stats['duplicates_skipped'] += 1
                return None
            
            # Mark as processed
            self.pdf_hashes.add(pdf_hash)
            self.downloaded_pdfs[pdf_url] = None  # Will be updated with file path
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            return None
    
    def is_user_guide_pdf(self, pdf_content: bytes) -> Tuple[bool, str]:
        """Enhanced user guide detection"""
        try:
            text_content = ""
            title = ""
            
            if PDF_LIBRARY == "PyMuPDF":
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                
                # Extract title from metadata
                metadata = doc.metadata
                if metadata.get('title'):
                    title = metadata['title']
                
                # Extract text from first few pages for analysis
                for page_num in range(min(5, len(doc))):
                    page = doc[page_num]
                    page_text = page.get_text().lower()
                    text_content += page_text
                    
                    # Try to extract title from first page if not in metadata
                    if page_num == 0 and not title:
                        lines = page_text.split('\n')
                        for line in lines[:15]:
                            line = line.strip()
                            if (len(line) > 5 and len(line) < 100 and 
                                any(word in line for word in ['guide', 'manual', 'instruction'])):
                                title = line
                                break
                
                doc.close()
                
            elif PDF_LIBRARY == "pdfplumber":
                import io
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    for page_num in range(min(5, len(pdf.pages))):
                        page = pdf.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text.lower()
                            
                            if page_num == 0 and not title:
                                lines = page_text.split('\n')
                                for line in lines[:15]:
                                    line = line.strip()
                                    if (len(line) > 5 and len(line) < 100 and 
                                        any(word in line.lower() for word in ['guide', 'manual', 'instruction'])):
                                        title = line
                                        break
            
            elif PDF_LIBRARY == "PyPDF2":
                import io
                from PyPDF2 import PdfReader
                
                reader = PdfReader(io.BytesIO(pdf_content))
                
                if reader.metadata and reader.metadata.title:
                    title = reader.metadata.title
                
                for page_num in range(min(5, len(reader.pages))):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text.lower()
            
            # Enhanced pattern matching
            user_guide_score = 0
            matched_patterns = []
            
            for pattern in self.user_guide_patterns:
                matches = len(re.findall(pattern, text_content, re.IGNORECASE))
                if matches > 0:
                    user_guide_score += matches
                    matched_patterns.append(pattern.replace(r'\s+', ' '))
            
            # Additional scoring factors
            if title:
                title_lower = title.lower()
                for pattern in self.user_guide_patterns:
                    if re.search(pattern, title_lower):
                        user_guide_score += 5  # Higher weight for title matches
                        matched_patterns.append(f"title: {pattern}")
            
            # Decision threshold
            is_user_guide = user_guide_score >= 2
            
            if is_user_guide:
                self.logger.info(f"User guide detected (score: {user_guide_score}): {matched_patterns}")
            
            return is_user_guide, title
            
        except Exception as e:
            self.logger.error(f"Error analyzing PDF content: {e}")
            return False, ""
    
    def get_product_name_from_url(self, url: str) -> str:
        """Extract clean product name from URL"""
        try:
            # Extract from URL path
            path = urlparse(url).path
            
            # Get the last part of the path
            product_part = path.split('/')[-1]
            
            # Clean up common URL artifacts
            product_name = re.sub(r'[^\w\-]', '_', product_part)
            product_name = re.sub(r'_+', '_', product_name)
            product_name = product_name.strip('_')
            
            # Ensure it's not empty
            if not product_name or len(product_name) < 2:
                product_name = f"product_{int(time.time())}"
            
            return product_name
            
        except Exception as e:
            self.logger.error(f"Error extracting product name from {url}: {e}")
            return f"unknown_product_{int(time.time())}"
    
    def save_user_guide_pdf(self, pdf_content: bytes, product_name: str, 
                           title: str = "", source_url: str = "") -> str:
        """Save user guide PDF with organized naming and metadata"""
        try:
            # Create clean filename
            if title and len(title.strip()) > 5:
                # Use title if available and meaningful
                clean_title = re.sub(r'[^\w\s\-]', '', title.strip())
                clean_title = re.sub(r'\s+', '_', clean_title)
                filename = f"{product_name}_{clean_title}.pdf"
            else:
                filename = f"{product_name}_user_guide.pdf"
            
            # Ensure filename length is reasonable
            if len(filename) > 150:
                filename = f"{product_name}_user_guide.pdf"
            
            filepath = self.output_dir / filename
            
            # Handle duplicates with counter
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                stem = original_filepath.stem
                suffix = original_filepath.suffix
                filepath = original_filepath.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Save PDF file
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            
            # Update tracking
            self.downloaded_pdfs[source_url] = str(filepath)
            
            # Save metadata file
            metadata_file = filepath.with_suffix('.json')
            metadata = {
                'filename': filepath.name,
                'product_name': product_name,
                'title': title,
                'source_url': source_url,
                'file_size': len(pdf_content),
                'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'pdf_hash': self.get_pdf_hash(pdf_content)
            }
            
            import json
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved user guide: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving user guide for {product_name}: {e}")
            return ""
    
    def process_product_page(self, product_url: str) -> Dict[str, any]:
        """Process a single product page for PDF extraction"""
        result = {
            'url': product_url,
            'product_name': '',
            'pdf_links_found': 0,
            'user_guides_downloaded': 0,
            'success': False,
            'error': None,
            'downloaded_files': []
        }
        
        try:
            # Skip if already processed
            if product_url in self.processed_urls:
                result['success'] = True
                result['error'] = 'Already processed'
                return result
            
            # Mark as processed
            self.processed_urls.add(product_url)
            
            # Extract product name
            product_name = self.get_product_name_from_url(product_url)
            result['product_name'] = product_name
            
            self.logger.info(f"Processing: {product_name} ({product_url})")
            
            # Extract PDF links
            pdf_links = self.extract_pdf_links_with_playwright(product_url)
            result['pdf_links_found'] = len(pdf_links)
            self.stats['pdf_links_found'] += len(pdf_links)
            
            if not pdf_links:
                self.logger.info(f"No PDF links found for {product_name}")
                result['success'] = True
                return result
            
            # Process each PDF link
            for pdf_url in pdf_links:
                try:
                    self.logger.info(f"Checking PDF: {pdf_url}")
                    
                    # Download PDF
                    pdf_content = self.download_pdf(pdf_url)
                    if not pdf_content:
                        continue
                    
                    # Check if it's a user guide
                    is_guide, title = self.is_user_guide_pdf(pdf_content)
                    
                    if is_guide:
                        # Save the user guide
                        saved_path = self.save_user_guide_pdf(
                            pdf_content, product_name, title, pdf_url
                        )
                        if saved_path:
                            result['user_guides_downloaded'] += 1
                            result['downloaded_files'].append(saved_path)
                            self.stats['user_guides_downloaded'] += 1
                            self.logger.info(f"✅ User guide saved: {saved_path}")
                    else:
                        self.logger.info(f"PDF not a user guide: {pdf_url}")
                    
                except Exception as pdf_error:
                    self.logger.error(f"Error processing PDF {pdf_url}: {pdf_error}")
                    continue
                
                # Rate limiting
                time.sleep(self.delay)
            
            result['success'] = True
            
        except Exception as e:
            error_msg = f"Error processing {product_url}: {e}"
            self.logger.error(error_msg)
            result['error'] = str(e)
            self.stats['errors'] += 1
        
        return result
    
    def run_comprehensive_extraction(self, max_pages: Optional[int] = None) -> Dict[str, any]:
        """Run comprehensive PDF extraction on all product pages"""
        
        start_time = time.time()
        
        self.logger.info("🚀 Starting Comprehensive PDF Extraction")
        self.logger.info("=" * 70)
        
        # Check dependencies
        if not PDF_LIBRARY:
            self.logger.error("❌ No PDF processing library available!")
            self.logger.error("Install: pip install PyMuPDF pdfplumber PyPDF2")
            return self.stats
        
        self.logger.info(f"📚 PDF Library: {PDF_LIBRARY}")
        self.logger.info(f"🌐 Web Scraping: {'Playwright' if PLAYWRIGHT_AVAILABLE else 'Requests+BeautifulSoup'}")
        
        # Load all product URLs
        product_urls = self.load_all_product_urls_from_sitemap()
        
        if not product_urls:
            self.logger.error("❌ No product URLs found!")
            return self.stats
        
        # Limit for testing if specified
        if max_pages:
            product_urls = product_urls[:max_pages]
            self.logger.info(f"📊 Limited to first {max_pages} products for testing")
        
        self.logger.info(f"📊 Processing {len(product_urls)} product pages")
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        self.logger.info(f"⏱️ Rate limiting: {self.delay}s between requests")
        
        # Process each product page
        processed_count = 0
        for i, product_url in enumerate(product_urls, 1):
            self.logger.info(f"\n[{i}/{len(product_urls)}] Processing page...")
            
            result = self.process_product_page(product_url)
            processed_count += 1
            self.stats['processed_product_urls'] = processed_count
            
            # Progress reporting
            if i % 25 == 0 or i == len(product_urls):
                elapsed = time.time() - start_time
                self.logger.info(f"Progress: {i}/{len(product_urls)} pages processed")
                self.logger.info(f"User guides found: {self.stats['user_guides_downloaded']}")
                self.logger.info(f"Elapsed time: {elapsed:.1f}s")
        
        # Final statistics
        self.stats['processing_time'] = time.time() - start_time
        return self.stats
    
    def print_final_summary(self):
        """Print comprehensive extraction summary"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("📊 COMPREHENSIVE PDF EXTRACTION SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"📄 Total product pages: {self.stats['total_product_urls']}")
        self.logger.info(f"✅ Pages processed: {self.stats['processed_product_urls']}")
        self.logger.info(f"🔗 PDF links found: {self.stats['pdf_links_found']}")
        self.logger.info(f"📚 User guides downloaded: {self.stats['user_guides_downloaded']}")
        self.logger.info(f"🔄 Duplicates skipped: {self.stats['duplicates_skipped']}")
        self.logger.info(f"❌ Errors: {self.stats['errors']}")
        self.logger.info(f"⏱️ Processing time: {self.stats['processing_time']:.1f}s")
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        
        if self.stats['user_guides_downloaded'] > 0:
            self.logger.info(f"\n🎉 SUCCESS! Downloaded {self.stats['user_guides_downloaded']} user guides!")
            self.logger.info(f"📈 Success rate: {(self.stats['user_guides_downloaded']/self.stats['processed_product_urls']*100):.1f}%")
        else:
            self.logger.info(f"\n⚠️ No user guides found. Check:")
            self.logger.info(f"   - PDF detection patterns")
            self.logger.info(f"   - Network connectivity") 
            self.logger.info(f"   - Website accessibility")


def main():
    """Main function"""
    
    print("🚀 Comprehensive PDF Extractor for K-Array Products")
    print("=" * 60)
    
    # Check available libraries
    print(f"📚 PDF Library: {PDF_LIBRARY or 'None available'}")
    print(f"🌐 Playwright: {'Available' if PLAYWRIGHT_AVAILABLE else 'Not available'}")
    print(f"🍲 BeautifulSoup: {'Available' if BS4_AVAILABLE else 'Not available'}")
    
    if not PDF_LIBRARY:
        print("\n❌ No PDF processing library found!")
        print("Install one of:")
        print("   pip install PyMuPDF          # Recommended")
        print("   pip install pdfplumber       # Alternative")
        print("   pip install PyPDF2           # Basic")
        return
    
    # Create extractor
    extractor = ComprehensivePDFExtractor()
    
    print(f"\n🚀 Starting comprehensive extraction...")
    print(f"⚠️  This will process ALL product pages from sitemap.xml")
    print(f"⏱️ Rate limiting: {extractor.delay}s between requests")
    
    # For initial testing, limit to first 10 pages
    # Remove max_pages parameter for full extraction
    stats = extractor.run_comprehensive_extraction(max_pages=10)  # Remove this limit for full run
    
    # Print final summary
    extractor.print_final_summary()


if __name__ == "__main__":
    main()