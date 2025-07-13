#!/usr/bin/env python3
"""
PDF to JSON Extractor for K-Array User Guides
Analyzes PDF files and generates structured JSON documents for RAG integration
"""

import os
import re
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_to_json_extraction.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFToJSONExtractor:
    """Extract K-Array PDF content and convert to structured JSON for RAG"""
    
    def __init__(self, pdf_dir: str = "data/user_guides", output_dir: str = "data"):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.extracted_count = 0
        self.processed_pdfs = []
        self.stats = {
            'total_pdfs': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_pages_processed': 0,
            'processing_time': 0
        }
        
        # Product identification patterns
        self.product_patterns = {
            'kommander': r'(?i)kommander[- ]?(ka\d+[a-z]*\+?(?:live)?)',
            'domino': r'(?i)domino[- ]?(kf\d+[a-z]*)',
            'kayman': r'(?i)kayman[- ]?(ky\d+[a-z]*)',
            'pinnacle': r'(?i)pinnacle[- ]?(kr?\d+[a-z]*)',
            'mugello': r'(?i)mugello[- ]?(kh\d+[a-z]*)',
            'python': r'(?i)python[- ]?(kp\d+[a-z]*)',
            'vyper': r'(?i)vyper[- ]?(kv\d+[a-z]*)',
            'lyzard': r'(?i)lyzard[- ]?(kz\d+[a-z]*)',
            'thunder': r'(?i)thunder[- ]?(k[ms][tcsp]?\d+[a-z]*)',
            'k-rack': r'(?i)k[- ]?rack[- ]?(m[- ]?\d+)'
        }
        
        # Technical specification patterns
        self.spec_patterns = {
            'frequency_response': [
                r'frequency response[:\s]*(\d+\s*hz\s*[-–]\s*\d+\.?\d*\s*khz)',
                r'freq\.?\s*response[:\s]*(\d+\s*hz\s*[-–]\s*\d+\.?\d*\s*khz)',
                r'(\d+\s*hz\s*[-–]\s*\d+\.?\d*\s*khz)\s*(?:\([^)]*\))?'
            ],
            'power': [
                r'(?:rated\s+)?power[:\s]*(\d+\.?\d*\s*w(?:att)?s?)',
                r'(\d+\.?\d*\s*w(?:att)?s?)\s*(?:rms|aes|rated)',
                r'max\.?\s*power[:\s]*(\d+\.?\d*\s*w(?:att)?s?)'
            ],
            'spl': [
                r'(?:max\.?\s*)?spl[:\s]*(\d+\.?\d*\s*db)',
                r'sound pressure level[:\s]*(\d+\.?\d*\s*db)',
                r'maximum\s+spl[:\s]*(\d+\.?\d*\s*db)'
            ],
            'impedance': [
                r'(?:nominal\s+)?impedance[:\s]*(\d+\.?\d*\s*[ωΩ](?:\s*[/,]\s*\d+\.?\d*\s*[ωΩ])?)',
                r'(\d+\.?\d*\s*[ωΩ](?:\s*[/,]\s*\d+\.?\d*\s*[ωΩ])?)\s*(?:nominal\s+)?impedance'
            ],
            'dimensions': [
                r'dimensions?[:\s]*(\d+\.?\d*\s*x\s*\d+\.?\d*\s*x\s*\d+\.?\d*\s*(?:mm|cm|in))',
                r'size[:\s]*(\d+\.?\d*\s*x\s*\d+\.?\d*\s*x\s*\d+\.?\d*\s*(?:mm|cm|in))',
                r'(\d+\.?\d*\s*x\s*\d+\.?\d*\s*x\s*\d+\.?\d*)\s*(?:mm|cm|in)'
            ],
            'weight': [
                r'weight[:\s]*(\d+\.?\d*\s*(?:kg|g|lb|lbs))',
                r'(\d+\.?\d*\s*(?:kg|g|lb|lbs))\s*weight'
            ],
            'coverage': [
                r'coverage[:\s]*(?:h\.?\s*)?(\d+°)(?:\s*x\s*(\d+°))?',
                r'dispersion[:\s]*(?:h\.?\s*)?(\d+°)(?:\s*x\s*(\d+°))?'
            ]
        }
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, int, Dict[str, Any]]:
        """Extract text content from PDF file"""
        try:
            text_content = ""
            page_count = 0
            metadata = {}
            
            if PDF_LIBRARY == "PyMuPDF":
                doc = fitz.open(str(pdf_path))
                page_count = len(doc)
                
                # Extract metadata
                meta = doc.metadata
                metadata = {
                    'title': meta.get('title', ''),
                    'author': meta.get('author', ''),
                    'subject': meta.get('subject', ''),
                    'creator': meta.get('creator', ''),
                    'producer': meta.get('producer', ''),
                    'creation_date': meta.get('creationDate', ''),
                    'modification_date': meta.get('modDate', '')
                }
                
                # Extract text from all pages
                for page_num in range(page_count):
                    page = doc[page_num]
                    page_text = page.get_text()
                    text_content += f"\n--- PAGE {page_num + 1} ---\n{page_text}"
                
                doc.close()
                
            elif PDF_LIBRARY == "pdfplumber":
                import io
                with pdfplumber.open(pdf_path) as pdf:
                    page_count = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text_content += f"\n--- PAGE {page_num + 1} ---\n{page_text}"
                            
            elif PDF_LIBRARY == "PyPDF2":
                import io
                from PyPDF2 import PdfReader
                
                reader = PdfReader(pdf_path)
                page_count = len(reader.pages)
                
                if reader.metadata:
                    metadata = {
                        'title': reader.metadata.title or '',
                        'author': reader.metadata.author or '',
                        'subject': reader.metadata.subject or '',
                        'creator': reader.metadata.creator or '',
                        'producer': reader.metadata.producer or ''
                    }
                
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- PAGE {page_num + 1} ---\n{page_text}"
            
            self.stats['total_pages_processed'] += page_count
            return text_content.strip(), page_count, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return "", 0, {}
    
    def identify_product(self, text: str, filename: str) -> Tuple[str, str, str]:
        """Identify product name, series, and model from text and filename"""
        
        # First try filename
        filename_clean = filename.lower().replace('_', '-').replace(' ', '-')
        
        for series, pattern in self.product_patterns.items():
            # Check filename
            match = re.search(pattern, filename_clean)
            if match:
                model = match.group(1).upper()
                return series.title(), model, f"Identified from filename: {filename}"
            
            # Check text content
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Take the most frequent match
                model = max(set(matches), key=matches.count).upper()
                return series.title(), model, f"Identified from content analysis"
        
        # Fallback: try to extract any model-like pattern
        model_patterns = [
            r'\b(K[A-Z]*\d+[A-Z]*(?:\+|LIVE)?)\b',
            r'\b([A-Z]{2,}\d+[A-Z]*)\b'
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, text.upper())
            if matches:
                model = max(set(matches), key=matches.count)
                return "Unknown", model, "Identified generic model pattern"
        
        return "Unknown", "Unknown", "Could not identify product"
    
    def extract_technical_specifications(self, text: str) -> Dict[str, Any]:
        """Extract technical specifications from text"""
        specs = {}
        
        # Clean text for better matching
        text_clean = re.sub(r'\s+', ' ', text.lower())
        
        for spec_type, patterns in self.spec_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_clean, re.IGNORECASE)
                if matches:
                    if spec_type == 'coverage' and len(matches[0]) == 2:
                        # Handle coverage with two values (H x V)
                        specs[spec_type] = {
                            'horizontal': matches[0][0],
                            'vertical': matches[0][1] if matches[0][1] else matches[0][0]
                        }
                    else:
                        # Take the first match for other specs
                        value = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        specs[spec_type] = value.strip()
        
        return specs
    
    def extract_key_sections(self, text: str) -> Dict[str, str]:
        """Extract key sections from the PDF text"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'introduction': r'(?i)(introduction|overview|general information).*?(?=\n[A-Z][^a-z]*\n|\n\d+\.|\Z)',
            'specifications': r'(?i)(technical specifications?|specifications?|tech specs).*?(?=\n[A-Z][^a-z]*\n|\n\d+\.|\Z)',
            'installation': r'(?i)(installation|mounting|setup).*?(?=\n[A-Z][^a-z]*\n|\n\d+\.|\Z)',
            'features': r'(?i)(features?|characteristics?).*?(?=\n[A-Z][^a-z]*\n|\n\d+\.|\Z)',
            'applications': r'(?i)(applications?|use cases?).*?(?=\n[A-Z][^a-z]*\n|\n\d+\.|\Z)',
            'troubleshooting': r'(?i)(troubleshooting|problems?|issues?).*?(?=\n[A-Z][^a-z]*\n|\n\d+\.|\Z)',
            'warranty': r'(?i)(warranty|guarantee).*?(?=\n[A-Z][^a-z]*\n|\n\d+\.|\Z)'
        }
        
        for section_name, pattern in section_patterns.items():
            matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
            if matches:
                # Take the longest match (most detailed)
                content = max(matches, key=len).strip()
                if len(content) > 50:  # Only include substantial content
                    sections[section_name] = content[:2000]  # Limit length
        
        return sections
    
    def generate_json_document(self, pdf_path: Path, text: str, metadata: Dict, page_count: int) -> Dict[str, Any]:
        """Generate structured JSON document from PDF content"""
        
        # Identify product
        series, model, identification_source = self.identify_product(text, pdf_path.stem)
        
        # Extract specifications
        specs = self.extract_technical_specifications(text)
        
        # Extract sections
        sections = self.extract_key_sections(text)
        
        # Generate unique ID
        pdf_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()[:8]
        doc_id = f"pdf_{len(self.processed_pdfs):03d}_{series.lower()}_{model.lower()}_{pdf_hash}"
        
        # Create base document structure
        document = {
            "id": doc_id,
            "source_type": "PDF_DOCUMENT",
            "source_file": str(pdf_path.name),
            "timestamp": datetime.now().isoformat(),
            "extraction_quality": "pdf_extracted",
            
            "metadata": {
                "category": "TECHNICAL_DOCUMENTATION",
                "subcategory": f"{series.upper()}_SERIES",
                "product_line": series,
                "model": model,
                "content_type": "user_guide",
                "manufacturer": "K-array",
                "identification_source": identification_source,
                "page_count": page_count,
                "file_size": pdf_path.stat().st_size,
                "pdf_metadata": metadata
            },
            
            "keywords": {
                "primary": [model, series, "user guide", "manual", "technical documentation"],
                "technical": list(specs.keys()),
                "document_type": ["pdf", "user_guide", "manual", "installation"],
                "unique_identifiers": [model.lower(), f"{series}-{model}".lower()]
            },
            
            "technical_specifications": specs,
            
            "content_sections": sections,
            
            "document_analysis": {
                "total_pages": page_count,
                "text_length": len(text),
                "specifications_found": len(specs),
                "sections_identified": len(sections),
                "extraction_confidence": self.calculate_extraction_confidence(text, specs, sections)
            },
            
            "embedding_optimized": {
                "searchable_text": self.create_searchable_text(series, model, specs, sections, text),
                "semantic_chunks": self.create_semantic_chunks(series, model, specs, sections),
                "qa_pairs": self.generate_qa_pairs(series, model, specs, sections)
            },
            
            "source_attributions": [
                {
                    "data": f"Technical documentation for {series} {model}",
                    "source": f"PDF User Guide: {pdf_path.name}"
                }
            ],
            
            "extraction_notes": {
                "pdf_library_used": PDF_LIBRARY,
                "extraction_method": "comprehensive_text_analysis",
                "quality_score": self.calculate_quality_score(text, specs, sections),
                "processing_date": datetime.now().isoformat()
            }
        }
        
        return document
    
    def calculate_extraction_confidence(self, text: str, specs: Dict, sections: Dict) -> float:
        """Calculate confidence score for extraction quality"""
        score = 0.0
        
        # Base score for text content
        if len(text) > 1000:
            score += 0.3
        elif len(text) > 500:
            score += 0.2
        elif len(text) > 100:
            score += 0.1
        
        # Score for technical specifications
        score += min(0.4, len(specs) * 0.05)
        
        # Score for identified sections
        score += min(0.3, len(sections) * 0.05)
        
        return min(1.0, score)
    
    def calculate_quality_score(self, text: str, specs: Dict, sections: Dict) -> str:
        """Calculate overall quality score"""
        confidence = self.calculate_extraction_confidence(text, specs, sections)
        
        if confidence >= 0.8:
            return "excellent"
        elif confidence >= 0.6:
            return "good"
        elif confidence >= 0.4:
            return "fair"
        elif confidence >= 0.2:
            return "basic"
        else:
            return "poor"
    
    def create_searchable_text(self, series: str, model: str, specs: Dict, sections: Dict, full_text: str) -> str:
        """Create optimized searchable text"""
        searchable_parts = [
            f"{series} {model} user guide technical documentation",
            " ".join(specs.values()) if specs else "",
            " ".join(sections.values())[:500] if sections else "",
            full_text[:1000]  # First 1000 chars of full text
        ]
        
        return " ".join(part for part in searchable_parts if part).strip()
    
    def create_semantic_chunks(self, series: str, model: str, specs: Dict, sections: Dict) -> List[str]:
        """Create semantic chunks for better retrieval"""
        chunks = []
        
        # Product identification chunk
        chunks.append(f"{series} {model} technical documentation and user guide.")
        
        # Specifications chunk
        if specs:
            spec_text = f"Technical specifications include: {', '.join(f'{k}: {v}' for k, v in specs.items())}."
            chunks.append(spec_text)
        
        # Section chunks
        for section_name, content in sections.items():
            if len(content) > 100:
                chunks.append(f"{section_name.title()}: {content[:300]}...")
        
        return chunks
    
    def generate_qa_pairs(self, series: str, model: str, specs: Dict, sections: Dict) -> List[Dict[str, str]]:
        """Generate Q&A pairs for better retrieval"""
        qa_pairs = []
        
        # Basic product questions
        qa_pairs.append({
            "question": f"What is the {model}?",
            "answer": f"The {model} is a {series} series product from K-Array.",
            "source": "Product identification from user guide"
        })
        
        # Specification questions
        for spec_name, spec_value in specs.items():
            question = f"What is the {spec_name.replace('_', ' ')} of the {model}?"
            qa_pairs.append({
                "question": question,
                "answer": f"The {spec_name.replace('_', ' ')} is {spec_value}.",
                "source": f"Technical specifications from user guide"
            })
        
        return qa_pairs
    
    def process_pdf_directory(self) -> List[Dict[str, Any]]:
        """Process all PDFs in the directory"""
        start_time = time.time()
        
        logger.info(f"🚀 Starting PDF to JSON extraction from {self.pdf_dir}")
        
        if not PDF_LIBRARY:
            logger.error("❌ No PDF processing library available!")
            logger.error("Install: pip install PyMuPDF pdfplumber PyPDF2")
            return []
        
        logger.info(f"📚 Using PDF library: {PDF_LIBRARY}")
        
        # Find all PDF files
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        if self.pdf_dir.joinpath("old").exists():
            pdf_files.extend(list(self.pdf_dir.joinpath("old").glob("*.pdf")))
        
        self.stats['total_pdfs'] = len(pdf_files)
        logger.info(f"📄 Found {len(pdf_files)} PDF files to process")
        
        extracted_documents = []
        
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
            
            try:
                # Extract text content
                text, page_count, metadata = self.extract_text_from_pdf(pdf_path)
                
                if not text or len(text) < 50:
                    logger.warning(f"Minimal text extracted from {pdf_path.name}")
                    self.stats['failed_extractions'] += 1
                    continue
                
                # Generate JSON document
                json_doc = self.generate_json_document(pdf_path, text, metadata, page_count)
                extracted_documents.append(json_doc)
                self.processed_pdfs.append(pdf_path.name)
                
                self.stats['successful_extractions'] += 1
                logger.info(f"✅ Successfully extracted: {json_doc['id']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {pdf_path.name}: {e}")
                self.stats['failed_extractions'] += 1
                continue
        
        self.stats['processing_time'] = time.time() - start_time
        return extracted_documents
    
    def save_extracted_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Save extracted documents as individual JSON files"""
        
        for doc in documents:
            # Create filename
            filename = f"extracted_pdf_{doc['id']}.json"
            filepath = self.output_dir / filename
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(doc, f, indent=2, ensure_ascii=False)
                
                logger.info(f"💾 Saved: {filepath.name}")
                
            except Exception as e:
                logger.error(f"Error saving {filename}: {e}")
    
    def generate_summary_report(self, documents: List[Dict[str, Any]]) -> str:
        """Generate extraction summary report"""
        
        report = f"""
📊 PDF to JSON Extraction Summary Report
{'='*60}

📈 Extraction Statistics:
- Total PDFs found: {self.stats['total_pdfs']}
- Successful extractions: {self.stats['successful_extractions']}
- Failed extractions: {self.stats['failed_extractions']}
- Total pages processed: {self.stats['total_pages_processed']}
- Processing time: {self.stats['processing_time']:.1f}s

📄 Documents Generated: {len(documents)}

🔍 Product Analysis:
"""
        
        # Analyze extracted products
        product_stats = {}
        for doc in documents:
            series = doc['metadata']['product_line']
            product_stats[series] = product_stats.get(series, 0) + 1
        
        for series, count in sorted(product_stats.items()):
            report += f"- {series}: {count} documents\n"
        
        # Quality analysis
        quality_stats = {}
        for doc in documents:
            quality = doc['extraction_notes']['quality_score']
            quality_stats[quality] = quality_stats.get(quality, 0) + 1
        
        report += f"\n📊 Quality Distribution:\n"
        for quality, count in sorted(quality_stats.items()):
            percentage = count / len(documents) * 100
            report += f"- {quality.title()}: {count} ({percentage:.1f}%)\n"
        
        # Success rate
        success_rate = self.stats['successful_extractions'] / self.stats['total_pdfs'] * 100
        report += f"\n🎯 Success Rate: {success_rate:.1f}%\n"
        
        return report
    
    def run_extraction(self) -> Dict[str, Any]:
        """Run complete PDF to JSON extraction process"""
        
        logger.info("🔄 Starting PDF to JSON extraction process")
        
        # Process all PDFs
        documents = self.process_pdf_directory()
        
        if not documents:
            logger.warning("⚠️ No documents were successfully extracted")
            return {"success": False, "message": "No documents extracted"}
        
        # Save documents
        self.save_extracted_documents(documents)
        
        # Generate and save report
        report = self.generate_summary_report(documents)
        logger.info(report)
        
        # Save report to file
        report_path = self.output_dir / "pdf_extraction_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 Report saved to: {report_path}")
        
        return {
            "success": True,
            "documents_extracted": len(documents),
            "stats": self.stats,
            "report_path": str(report_path)
        }


def main():
    """Main function"""
    print("🔄 PDF to JSON Extractor for K-Array Documentation")
    print("=" * 60)
    
    # Check dependencies
    if not PDF_LIBRARY:
        print("❌ No PDF processing library found!")
        print("Install: pip install PyMuPDF pdfplumber PyPDF2")
        return
    
    print(f"📚 Using PDF library: {PDF_LIBRARY}")
    
    # Create extractor and run
    extractor = PDFToJSONExtractor()
    results = extractor.run_extraction()
    
    if results["success"]:
        print(f"\n✅ Extraction completed successfully!")
        print(f"📄 Documents extracted: {results['documents_extracted']}")
        print(f"📊 Processing time: {results['stats']['processing_time']:.1f}s")
        print(f"📈 Success rate: {results['stats']['successful_extractions']/results['stats']['total_pdfs']*100:.1f}%")
    else:
        print(f"\n❌ Extraction failed: {results['message']}")


if __name__ == "__main__":
    main()