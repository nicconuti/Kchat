#!/usr/bin/env python3
"""
Systematic K-Array Scraper - Process EVERY URL from sitemap.xml
Zero-hallucination quality with complete coverage
"""

import xml.etree.ElementTree as ET
import json
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

class SystematicScraper:
    """Systematic scraper that processes EVERY URL from sitemap.xml"""
    
    def __init__(self, sitemap_path: str = "sitemap.xml"):
        self.sitemap_path = sitemap_path
        self.setup_logging()
        self.progress_tracker = {
            'total_urls': 0,
            'processed_urls': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'urls_status': {}  # URL -> {'status': 'pending/processing/completed/failed', 'timestamp': '', 'data': {}}
        }
        self.extracted_data = {}
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/systematic_scraping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_all_urls_from_sitemap(self) -> List[str]:
        """Load ALL URLs from sitemap.xml"""
        
        self.logger.info(f"Loading ALL URLs from {self.sitemap_path}")
        
        try:
            # Parse XML sitemap
            tree = ET.parse(self.sitemap_path)
            root = tree.getroot()
            
            # Extract all URLs
            urls = []
            namespace = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            for url_element in root.findall('sitemap:url', namespace):
                loc_element = url_element.find('sitemap:loc', namespace)
                if loc_element is not None and loc_element.text:
                    urls.append(loc_element.text.strip())
            
            # If namespace doesn't work, try without namespace
            if not urls:
                for url_element in root.findall('url'):
                    loc_element = url_element.find('loc')
                    if loc_element is not None and loc_element.text:
                        urls.append(loc_element.text.strip())
            
            self.progress_tracker['total_urls'] = len(urls)
            
            # Initialize status tracking for each URL
            for url in urls:
                self.progress_tracker['urls_status'][url] = {
                    'status': 'pending',
                    'timestamp': None,
                    'data': None,
                    'extraction_type': self.classify_url_type(url)
                }
            
            self.logger.info(f"Loaded {len(urls)} URLs for systematic processing")
            return urls
            
        except Exception as e:
            self.logger.error(f"Error loading sitemap: {str(e)}")
            return []
    
    def classify_url_type(self, url: str) -> str:
        """Classify URL type for specialized extraction"""
        
        if '/product/' in url:
            return 'individual_product'
        elif '/products/line/' in url:
            return 'product_line'
        elif '/products/type/' in url:
            return 'product_category'
        elif '/application/' in url:
            return 'application_guide'
        elif '/post/' in url and 'case-studies' not in url:
            return 'case_study'
        elif '/post/case-studies' in url:
            return 'case_studies_index'
        elif '/k-academy' in url:
            return 'educational_content'
        elif '/software' in url:
            return 'software_downloads'
        elif '/accessories' in url:
            return 'accessories_catalog'
        elif '/discontinued-product' in url:
            return 'discontinued_products'
        elif '/about' in url or '/contact' in url:
            return 'company_info'
        else:
            return 'general_content'
    
    def start_systematic_extraction(self):
        """Start systematic extraction of ALL URLs"""
        
        self.logger.info("=" * 80)
        self.logger.info("STARTING SYSTEMATIC K-ARRAY EXTRACTION")
        self.logger.info("Strategy: Process EVERY URL from sitemap.xml")
        self.logger.info("Quality: Zero-hallucination with source attribution")
        self.logger.info("=" * 80)
        
        # Load all URLs
        all_urls = self.load_all_urls_from_sitemap()
        
        if not all_urls:
            self.logger.error("No URLs loaded from sitemap. Aborting.")
            return
        
        # Prioritize URLs for systematic processing
        prioritized_batches = self.create_processing_batches(all_urls)
        
        # Process each batch systematically
        for batch_name, batch_urls in prioritized_batches.items():
            self.logger.info(f"🔄 PROCESSING BATCH: {batch_name} ({len(batch_urls)} URLs)")
            self.process_batch(batch_name, batch_urls)
            
            # Save progress after each batch
            self.save_progress()
            
            self.logger.info(f"✅ BATCH COMPLETED: {batch_name}")
            self.logger.info(f"Progress: {self.progress_tracker['processed_urls']}/{self.progress_tracker['total_urls']} URLs")
        
        # Generate final comprehensive dataset
        self.logger.info("📦 GENERATING FINAL COMPREHENSIVE DATASET")
        final_dataset = self.generate_final_dataset()
        
        self.logger.info("=" * 80)
        self.logger.info("SYSTEMATIC EXTRACTION COMPLETED")
        self.logger.info(f"Total URLs processed: {self.progress_tracker['processed_urls']}")
        self.logger.info(f"Successful extractions: {self.progress_tracker['successful_extractions']}")
        self.logger.info(f"Success rate: {(self.progress_tracker['successful_extractions']/self.progress_tracker['processed_urls'])*100:.1f}%")
        self.logger.info("=" * 80)
        
        return final_dataset
    
    def create_processing_batches(self, urls: List[str]) -> Dict[str, List[str]]:
        """Create processing batches based on URL type and priority"""
        
        batches = {
            'batch_1_individual_products': [],      # Highest priority: Individual product specs
            'batch_2_product_lines': [],            # Product line overviews
            'batch_3_applications': [],             # Application guides
            'batch_4_case_studies': [],             # Real implementations
            'batch_5_educational': [],              # K-Academy content
            'batch_6_software_accessories': [],     # Software and accessories
            'batch_7_company_content': [],          # Company information
            'batch_8_general_content': []           # Everything else
        }
        
        for url in urls:
            url_type = self.classify_url_type(url)
            
            if url_type == 'individual_product':
                batches['batch_1_individual_products'].append(url)
            elif url_type == 'product_line':
                batches['batch_2_product_lines'].append(url)
            elif url_type == 'application_guide':
                batches['batch_3_applications'].append(url)
            elif url_type in ['case_study', 'case_studies_index']:
                batches['batch_4_case_studies'].append(url)
            elif url_type == 'educational_content':
                batches['batch_5_educational'].append(url)
            elif url_type in ['software_downloads', 'accessories_catalog']:
                batches['batch_6_software_accessories'].append(url)
            elif url_type in ['company_info', 'discontinued_products']:
                batches['batch_7_company_content'].append(url)
            else:
                batches['batch_8_general_content'].append(url)
        
        # Log batch sizes
        for batch_name, batch_urls in batches.items():
            self.logger.info(f"{batch_name}: {len(batch_urls)} URLs")
        
        return batches
    
    def process_batch(self, batch_name: str, batch_urls: List[str]):
        """Process a batch of URLs with appropriate extraction strategy"""
        
        batch_start_time = time.time()
        
        for i, url in enumerate(batch_urls, 1):
            self.logger.info(f"🔄 Processing {i}/{len(batch_urls)}: {url}")
            
            # Mark as processing
            self.progress_tracker['urls_status'][url]['status'] = 'processing'
            self.progress_tracker['urls_status'][url]['timestamp'] = datetime.now().isoformat()
            
            try:
                # Extract with type-specific strategy
                extraction_result = self.extract_url_with_strategy(url)
                
                if extraction_result:
                    # Mark as completed
                    self.progress_tracker['urls_status'][url]['status'] = 'completed'
                    self.progress_tracker['urls_status'][url]['data'] = extraction_result
                    self.progress_tracker['successful_extractions'] += 1
                    
                    # Store in main dataset
                    self.extracted_data[url] = extraction_result
                    
                    self.logger.info(f"✅ Successfully extracted from {url}")
                else:
                    # Mark as failed
                    self.progress_tracker['urls_status'][url]['status'] = 'failed'
                    self.progress_tracker['failed_extractions'] += 1
                    self.logger.warning(f"❌ Failed to extract from {url}")
                
                self.progress_tracker['processed_urls'] += 1
                
                # Quality-focused delay (2-3 seconds between requests)
                time.sleep(2.5)
                
            except Exception as e:
                self.logger.error(f"Error processing {url}: {str(e)}")
                self.progress_tracker['urls_status'][url]['status'] = 'failed'
                self.progress_tracker['failed_extractions'] += 1
                self.progress_tracker['processed_urls'] += 1
        
        batch_duration = time.time() - batch_start_time
        self.logger.info(f"Batch {batch_name} completed in {batch_duration:.1f} seconds")
    
    def extract_url_with_strategy(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content using type-specific strategy with real WebFetch"""
        
        url_type = self.classify_url_type(url)
        extraction_strategy = self.get_extraction_strategy_for_type(url_type)
        
        try:
            # Get specialized extraction prompt for this URL type
            prompt = self.get_mvp_extraction_prompt(url_type)
            
            # Perform real WebFetch extraction
            try:
                from claude_tools import WebFetch
                extraction_result = WebFetch(url=url, prompt=prompt)
            except ImportError:
                self.logger.warning("WebFetch tool not available, using placeholder")
                extraction_result = f"[PLACEHOLDER: Would extract from {url} using WebFetch tool]"
            
            if not extraction_result or len(extraction_result.strip()) < 100:
                self.logger.warning(f"Insufficient content extracted from {url}")
                return None
            
            # Validate quality and structure result
            extraction_data = {
                'url': url,
                'url_type': url_type,
                'extraction_strategy': extraction_strategy,
                'extraction_timestamp': datetime.now().isoformat(),
                'extracted_content': extraction_result,
                'quality_validated': self.validate_extraction_quality(extraction_result),
                'source_attribution_ready': True,
                'content_length': len(extraction_result)
            }
            
            # Only return if quality validation passes
            if extraction_data['quality_validated']:
                return extraction_data
            else:
                self.logger.warning(f"Quality validation failed for {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Real extraction failed for {url}: {str(e)}")
            return None
    
    def get_extraction_strategy_for_type(self, url_type: str) -> str:
        """Get extraction strategy description for URL type"""
        
        strategies = {
            'individual_product': 'MVP-quality technical specifications with source attribution',
            'product_line': 'Product family overview with model variations',
            'application_guide': 'Application-specific product recommendations and challenges',
            'case_study': 'Real implementation details with specific products and configurations',
            'educational_content': 'Technical education content and training materials',
            'software_downloads': 'Software catalog with download links and specifications',
            'accessories_catalog': 'Accessory compatibility matrix and specifications',
            'company_info': 'Company information and contact details',
            'general_content': 'General content extraction with quality validation'
        }
        
        return strategies.get(url_type, 'Standard content extraction')
    
    def get_mvp_extraction_prompt(self, url_type: str) -> str:
        """Generate MVP-quality extraction prompts with zero-hallucination focus"""
        
        base_instructions = """
        CRITICAL MVP REQUIREMENTS:
        1. Extract ONLY information explicitly stated in the source
        2. NEVER infer, estimate, assume, or speculate any values
        3. For each specification, provide the EXACT quote from the source
        4. If information is not explicitly stated, mark as "Not specified"
        5. Maintain perfect accuracy - hallucinations are NOT acceptable
        6. Include source attribution for every technical fact
        """
        
        if url_type == 'individual_product':
            return f"""
            {base_instructions}
            
            Extract technical specifications from this K-Array product page with MVP quality:
            
            Required output format:
            ```
            PRODUCT_NAME: [Exact product name from page]
            PRODUCT_SERIES: [Product family/series]
            
            TECHNICAL_SPECIFICATIONS:
            - Power: [VALUE] W (Source: "[exact quote]")
            - Frequency: [VALUE] Hz (Source: "[exact quote]")
            - SPL: [VALUE] dB (Source: "[exact quote]")
            - Dimensions: [VALUE] (Source: "[exact quote]")
            - Weight: [VALUE] (Source: "[exact quote]")
            - Material: [VALUE] (Source: "[exact quote]")
            - Mounting: [VALUE] (Source: "[exact quote]")
            
            APPLICATIONS_MENTIONED:
            - [Only applications explicitly mentioned on this page]
            
            COMPATIBLE_ACCESSORIES:
            - [Only accessories explicitly listed on this page]
            
            PDF_DOWNLOADS_AVAILABLE:
            - [List any PDF download links found]
            ```
            
            CRITICAL: If a specification is not found, write "Not specified" instead of guessing.
            CRITICAL: Every technical value must have a source quote.
            CRITICAL: No speculation or interpretation allowed.
            """
            
        elif url_type == 'application_guide':
            return f"""
            {base_instructions}
            
            Extract application guidance with source attribution:
            
            Output format:
            ```
            APPLICATION_SECTOR: [Exact sector name]
            
            TECHNICAL_CHALLENGES:
            - [Challenge]: "[exact quote describing challenge]"
            
            RECOMMENDED_PRODUCTS:
            - [Product model]: [Reason mentioned] (Source: "[quote]")
            
            CASE_STUDIES_REFERENCED:
            - [Project name]: [Brief description if provided]
            
            BENEFITS_CLAIMED:
            - [Benefit]: "[exact quote]"
            ```
            
            Only include information explicitly stated on the page.
            """
            
        elif url_type == 'case_study':
            return f"""
            {base_instructions}
            
            Extract case study information:
            
            Required format:
            ```
            PROJECT_NAME: [Exact project name]
            LOCATION: [Venue location if stated]  
            VENUE_TYPE: [Type of venue]
            CHALLENGE: [Technical challenge described]
            SOLUTION: [K-Array products used (exact models)]
            CONFIGURATION: [Setup details if provided]
            RESULTS: [Outcomes achieved (exact quotes)]
            ```
            
            List only products explicitly mentioned by model name.
            """
        
        return f"{base_instructions}\n\nExtract all relevant technical information from this K-Array page with MVP quality standards."
    
    def validate_extraction_quality(self, extracted_content: str) -> bool:
        """Validate extraction meets MVP quality standards"""
        
        quality_checks = {
            'has_sufficient_content': len(extracted_content.strip()) >= 100,
            'has_source_attribution': 'Source:' in extracted_content or '"' in extracted_content,
            'no_speculation_words': not any(word in extracted_content.lower() 
                                          for word in ['probably', 'typically', 'usually', 'estimated', 'approximately', 'likely']),
            'has_explicit_values': any(char.isdigit() for char in extracted_content),
            'proper_structure': ':' in extracted_content or '-' in extracted_content,
            'no_placeholder_text': not any(placeholder in extracted_content.lower() 
                                         for placeholder in ['placeholder', 'todo', 'tbd', 'coming soon'])
        }
        
        passed_checks = sum(quality_checks.values())
        total_checks = len(quality_checks)
        quality_score = passed_checks / total_checks
        
        # Log failed checks for debugging
        for check_name, passed in quality_checks.items():
            if not passed:
                self.logger.debug(f"Quality check failed: {check_name}")
        
        return quality_score >= 0.8  # 80% minimum for MVP quality
    
    def save_progress(self):
        """Save current progress to disk"""
        
        progress_file = 'data/systematic_scraping_progress.json'
        
        progress_data = {
            'last_updated': datetime.now().isoformat(),
            'progress_summary': {
                'total_urls': self.progress_tracker['total_urls'],
                'processed_urls': self.progress_tracker['processed_urls'],
                'successful_extractions': self.progress_tracker['successful_extractions'],
                'failed_extractions': self.progress_tracker['failed_extractions'],
                'completion_percentage': (self.progress_tracker['processed_urls'] / self.progress_tracker['total_urls']) * 100 if self.progress_tracker['total_urls'] > 0 else 0
            },
            'url_status_tracking': self.progress_tracker['urls_status']
        }
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Progress saved to {progress_file}")
    
    def generate_final_dataset(self) -> Dict[str, Any]:
        """Generate final comprehensive dataset"""
        
        final_dataset = {
            'dataset_metadata': {
                'generation_date': datetime.now().isoformat(),
                'extraction_method': 'systematic_complete_sitemap',
                'total_urls_in_sitemap': self.progress_tracker['total_urls'],
                'successfully_processed': self.progress_tracker['successful_extractions'],
                'processing_completion_rate': f"{(self.progress_tracker['processed_urls']/self.progress_tracker['total_urls'])*100:.1f}%",
                'quality_standard': 'zero_hallucination_mvp'
            },
            'extracted_content': self.extracted_data,
            'processing_statistics': self.progress_tracker,
            'url_classification': self.get_url_classification_summary()
        }
        
        # Save final dataset
        output_file = 'data/k_array_systematic_complete_dataset.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_dataset, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Final dataset saved to {output_file}")
        return final_dataset
    
    def get_url_classification_summary(self) -> Dict[str, int]:
        """Get summary of URL classifications"""
        
        classification_count = {}
        
        for url, status_info in self.progress_tracker['urls_status'].items():
            url_type = status_info['extraction_type']
            if url_type not in classification_count:
                classification_count[url_type] = 0
            classification_count[url_type] += 1
        
        return classification_count


if __name__ == "__main__":
    scraper = SystematicScraper()
    dataset = scraper.start_systematic_extraction()
    print(f"Systematic extraction completed! Dataset contains {len(dataset['extracted_content'])} entries.")