#!/usr/bin/env python3
"""
Enhanced JSON Documentation Improver
Analyzes and improves PDF documentation sections in K-Array JSON files
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('json_documentation_enhancement.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JSONDocumentationEnhancer:
    """Enhanced documentation analyzer and improver for K-Array JSON files"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.enhanced_count = 0
        self.analyzed_count = 0
        self.issues_found = []
        
        # Standard documentation templates by product type
        self.documentation_templates = {
            "amplifiers": [
                "Datasheet", "User Guide", "Quick Start Guide", 
                "Amp-to-speaker matching table", "CE Declaration of Conformity"
            ],
            "speakers": [
                "Datasheet", "User Guide", "EASE Data", "DWG 3D", "DXF 2D", 
                "PDF 3D", "Layout", "Architects Specs", "CE Declaration of Conformity"
            ],
            "line_arrays": [
                "Datasheet", "User Guide", "EASE & EASE Focus Data", "Preset",
                "DWG 3D", "DXF 2D", "3DS 3D", "PDF 3D", "Layout", 
                "Architects Specs", "CE Declaration of Conformity", "BIM files"
            ],
            "systems": [
                "System Configuration Guide", "User Guide", "Installation Manual",
                "DWG 3D", "Layout", "CE Declaration of Conformity"
            ]
        }
        
        # Known PDF link patterns from K-Array website
        self.pdf_url_patterns = [
            r'https://www\.k-array\.com/(?:sites/default/files|downloads)/.*\.pdf',
            r'https://www\.k-array\.com/.*download.*\.pdf',
            r'/sites/default/files/.*\.pdf'
        ]
    
    def analyze_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single JSON file for documentation quality"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analysis = {
                'file_path': str(file_path),
                'product_name': data.get('metadata', {}).get('model', 'Unknown'),
                'product_line': data.get('metadata', {}).get('product_line', 'Unknown'),
                'has_documentation_section': 'documentation' in data,
                'documentation_quality': 'unknown',
                'issues': [],
                'suggestions': [],
                'current_docs': []
            }
            
            # Check documentation section
            if 'documentation' in data:
                doc_section = data['documentation']
                
                if 'available_documents' in doc_section:
                    analysis['current_docs'] = doc_section['available_documents']
                    analysis['documentation_quality'] = self.rate_documentation_quality(
                        doc_section['available_documents']
                    )
                else:
                    analysis['issues'].append("Missing 'available_documents' field")
                    analysis['documentation_quality'] = 'poor'
                
                # Check for actual PDF URLs
                if not self.has_pdf_urls(data):
                    analysis['issues'].append("No actual PDF URLs found - only document type names")
                    analysis['suggestions'].append("Extract direct PDF download links")
                    
            else:
                analysis['issues'].append("Missing entire documentation section")
                analysis['documentation_quality'] = 'none'
                analysis['suggestions'].append("Add complete documentation section")
            
            # Product-specific analysis
            product_type = self.detect_product_type(data)
            expected_docs = self.documentation_templates.get(product_type, [])
            
            if analysis['current_docs']:
                missing_docs = set(expected_docs) - set(analysis['current_docs'])
                if missing_docs:
                    analysis['suggestions'].append(f"Consider adding: {', '.join(missing_docs)}")
            
            self.analyzed_count += 1
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'error': str(e),
                'documentation_quality': 'error'
            }
    
    def detect_product_type(self, data: Dict) -> str:
        """Detect product type based on content"""
        metadata = data.get('metadata', {})
        keywords = data.get('keywords', {}).get('primary', [])
        
        product_line = metadata.get('product_line', '').lower()
        model = metadata.get('model', '').lower()
        
        # Check for amplifiers
        if any(word in ' '.join(keywords).lower() for word in ['amplifier', 'amp', 'kommander']):
            return 'amplifiers'
        
        # Check for line arrays
        if any(word in ' '.join(keywords).lower() for word in ['line array', 'python', 'kobra']):
            return 'line_arrays'
        
        # Check for systems
        if any(word in model for word in ['syst', 'system', 'kit']):
            return 'systems'
        
        # Default to speakers
        return 'speakers'
    
    def rate_documentation_quality(self, documents: List[str]) -> str:
        """Rate documentation quality based on completeness"""
        if not documents:
            return 'none'
        
        # Essential documents
        essential_docs = ['datasheet', 'user guide']
        has_essential = any(
            any(essential.lower() in doc.lower() for essential in essential_docs)
            for doc in documents
        )
        
        if len(documents) >= 8 and has_essential:
            return 'excellent'
        elif len(documents) >= 5 and has_essential:
            return 'good'
        elif len(documents) >= 3:
            return 'fair'
        elif has_essential:
            return 'basic'
        else:
            return 'poor'
    
    def has_pdf_urls(self, data: Dict) -> bool:
        """Check if the JSON contains actual PDF URLs"""
        content_str = json.dumps(data).lower()
        
        # Look for PDF URLs
        for pattern in self.pdf_url_patterns:
            if re.search(pattern.lower(), content_str):
                return True
        
        # Look for common PDF indicators
        pdf_indicators = [
            'https://', 'www.k-array.com', '.pdf', 'download'
        ]
        
        # Need at least 2 indicators to suggest actual URLs
        found_indicators = sum(1 for indicator in pdf_indicators if indicator in content_str)
        return found_indicators >= 2
    
    def enhance_json_file(self, file_path: Path, analysis: Dict[str, Any]) -> bool:
        """Enhance a JSON file based on analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            enhanced = False
            
            # Add missing documentation section
            if not analysis['has_documentation_section']:
                product_type = self.detect_product_type(data)
                expected_docs = self.documentation_templates.get(product_type, 
                                self.documentation_templates['speakers'])
                
                data['documentation'] = {
                    "available_documents": expected_docs,
                    "download_links": {
                        "note": "Direct PDF URLs need to be extracted from product page"
                    },
                    "warranty": "Available (details not specified)",
                    "source": "Standard documentation template applied based on product type."
                }
                enhanced = True
                logger.info(f"Added documentation section to {file_path.name}")
            
            # Enhance existing documentation section
            elif 'documentation' in data:
                doc_section = data['documentation']
                
                # Add download_links structure if missing
                if 'download_links' not in doc_section:
                    doc_section['download_links'] = {
                        "note": "Direct PDF URLs need to be extracted from product page",
                        "extraction_needed": True
                    }
                    enhanced = True
                
                # Add metadata about documentation quality
                if 'quality_assessment' not in doc_section:
                    doc_section['quality_assessment'] = {
                        "completeness_score": analysis['documentation_quality'],
                        "total_documents": len(analysis['current_docs']),
                        "has_direct_urls": self.has_pdf_urls(data),
                        "enhancement_suggestions": analysis['suggestions']
                    }
                    enhanced = True
            
            # Save enhanced file
            if enhanced:
                # Create backup
                backup_path = file_path.with_suffix('.json.backup')
                if not backup_path.exists():
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Save enhanced version
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.enhanced_count += 1
                logger.info(f"Enhanced {file_path.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enhancing {file_path}: {e}")
            return False
    
    def analyze_all_files(self) -> Dict[str, Any]:
        """Analyze all JSON files in the data directory"""
        json_files = list(self.data_dir.glob("extracted_data_*.json"))
        
        logger.info(f"Found {len(json_files)} JSON files to analyze")
        
        analyses = []
        quality_stats = {'none': 0, 'poor': 0, 'basic': 0, 'fair': 0, 'good': 0, 'excellent': 0, 'error': 0}
        
        for file_path in sorted(json_files):
            analysis = self.analyze_json_file(file_path)
            analyses.append(analysis)
            
            quality = analysis.get('documentation_quality', 'error')
            quality_stats[quality] += 1
            
            # Track issues
            if analysis.get('issues'):
                self.issues_found.extend([
                    f"{file_path.name}: {issue}" for issue in analysis['issues']
                ])
        
        return {
            'total_files': len(json_files),
            'analyses': analyses,
            'quality_statistics': quality_stats,
            'common_issues': self.issues_found
        }
    
    def generate_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate comprehensive analysis report"""
        stats = analysis_results['quality_statistics']
        total = analysis_results['total_files']
        
        report = f"""
📊 K-Array JSON Documentation Quality Analysis Report
{'='*60}

📈 Quality Distribution:
- Excellent: {stats['excellent']} ({stats['excellent']/total*100:.1f}%)
- Good: {stats['good']} ({stats['good']/total*100:.1f}%)
- Fair: {stats['fair']} ({stats['fair']/total*100:.1f}%)
- Basic: {stats['basic']} ({stats['basic']/total*100:.1f}%)
- Poor: {stats['poor']} ({stats['poor']/total*100:.1f}%)
- None: {stats['none']} ({stats['none']/total*100:.1f}%)
- Errors: {stats['error']} ({stats['error']/total*100:.1f}%)

🔍 Files Analyzed: {self.analyzed_count}
✨ Files Enhanced: {self.enhanced_count}

📋 Most Common Issues:
"""
        
        # Count issue frequency
        issue_counts = {}
        for issue in self.issues_found:
            issue_type = issue.split(': ', 1)[1] if ': ' in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            report += f"- {issue}: {count} files\n"
        
        # Product line analysis
        product_lines = {}
        for analysis in analysis_results['analyses']:
            line = analysis.get('product_line', 'Unknown')
            quality = analysis.get('documentation_quality', 'unknown')
            if line not in product_lines:
                product_lines[line] = {'total': 0, 'good_quality': 0}
            product_lines[line]['total'] += 1
            if quality in ['good', 'excellent']:
                product_lines[line]['good_quality'] += 1
        
        report += "\n📊 Quality by Product Line:\n"
        for line, stats in sorted(product_lines.items()):
            percentage = stats['good_quality'] / stats['total'] * 100 if stats['total'] > 0 else 0
            report += f"- {line}: {stats['good_quality']}/{stats['total']} ({percentage:.1f}%) good quality\n"
        
        return report
    
    def run_enhancement(self, enhance_files: bool = True) -> Dict[str, Any]:
        """Run complete analysis and enhancement process"""
        logger.info("🚀 Starting JSON Documentation Analysis and Enhancement")
        
        # Analyze all files
        analysis_results = self.analyze_all_files()
        
        # Enhance files if requested
        if enhance_files:
            logger.info("✨ Enhancing files with poor documentation...")
            
            for analysis in analysis_results['analyses']:
                if analysis['documentation_quality'] in ['none', 'poor', 'basic']:
                    file_path = Path(analysis['file_path'])
                    self.enhance_json_file(file_path, analysis)
        
        # Generate and display report
        report = self.generate_report(analysis_results)
        logger.info(report)
        
        # Save detailed report
        report_path = self.data_dir / "documentation_quality_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
            # Add detailed file analysis
            f.write(f"\n\n## Detailed File Analysis\n\n")
            for analysis in analysis_results['analyses']:
                f.write(f"### {Path(analysis['file_path']).name}\n")
                f.write(f"- Product: {analysis.get('product_name', 'Unknown')}\n")
                f.write(f"- Line: {analysis.get('product_line', 'Unknown')}\n")
                f.write(f"- Quality: {analysis.get('documentation_quality', 'Unknown')}\n")
                f.write(f"- Current docs: {len(analysis.get('current_docs', []))}\n")
                if analysis.get('issues'):
                    f.write(f"- Issues: {', '.join(analysis['issues'])}\n")
                if analysis.get('suggestions'):
                    f.write(f"- Suggestions: {', '.join(analysis['suggestions'])}\n")
                f.write("\n")
        
        logger.info(f"📄 Detailed report saved to: {report_path}")
        
        return {
            'analysis_results': analysis_results,
            'enhanced_count': self.enhanced_count,
            'report_path': str(report_path)
        }


def main():
    """Main function"""
    print("🔍 K-Array JSON Documentation Quality Analyzer & Enhancer")
    print("=" * 60)
    
    enhancer = JSONDocumentationEnhancer()
    
    # Run analysis and enhancement
    results = enhancer.run_enhancement(enhance_files=True)
    
    print(f"\n✅ Analysis Complete!")
    print(f"📊 Files analyzed: {enhancer.analyzed_count}")
    print(f"✨ Files enhanced: {enhancer.enhanced_count}")
    print(f"📄 Report: {results['report_path']}")


if __name__ == "__main__":
    main()