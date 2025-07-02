#!/usr/bin/env python3
"""
Manager per il sistema di estrazione avanzata K-Array.
Coordina l'estrazione, il processing e l'integrazione nella knowledge base.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import shutil

from advanced_extractor import AdvancedExtractor, ExtractedDocument, KeywordExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractionManager:
    """Manager principale per coordinare tutto il processo di estrazione."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("karray_rag/data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.advanced_knowledge_file = self.output_dir / "karray_advanced_knowledge.jsonl"
        self.main_knowledge_file = self.output_dir / "karray_knowledge.jsonl"
        self.backup_dir = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.extraction_stats = {}
        
    async def run_full_extraction(self, incremental: bool = True) -> Dict[str, Any]:
        """
        Esegue l'estrazione completa del sito K-Array.
        
        Args:
            incremental: Se True, aggiunge ai dati esistenti. Se False, sostituisce tutto.
        """
        logger.info("🚀 Avvio estrazione completa K-Array")
        
        start_time = datetime.now()
        
        # Backup dei dati esistenti se incremental
        if incremental and self.main_knowledge_file.exists():
            await self._create_backup()
        
        try:
            # Estrazione avanzata
            async with AdvancedExtractor() as extractor:
                documents = await extractor.extract_all()
                
                # Salva i documenti estratti
                await extractor.save_to_jsonl(self.advanced_knowledge_file)
                
                # Statistiche dell'estrazione
                self.extraction_stats = {
                    'total_documents': len(documents),
                    'categories': self._analyze_categories(documents),
                    'product_coverage': self._analyze_product_coverage(documents),
                    'quality_scores': self._analyze_quality(documents),
                    'extractor_stats': extractor.stats,
                    'extraction_time': (datetime.now() - start_time).total_seconds(),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Integra con la knowledge base esistente
                if incremental:
                    await self._integrate_with_existing(documents)
                else:
                    await self._replace_knowledge_base(documents)
                
                # Genera report
                report = await self._generate_extraction_report()
                
                logger.info(f"✅ Estrazione completata in {self.extraction_stats['extraction_time']:.1f} secondi")
                
                return {
                    'success': True,
                    'documents_extracted': len(documents),
                    'statistics': self.extraction_stats,
                    'report': report
                }
                
        except Exception as e:
            logger.error(f"❌ Errore durante l'estrazione: {e}")
            return {
                'success': False,
                'error': str(e),
                'statistics': self.extraction_stats
            }
    
    async def _create_backup(self):
        """Crea un backup della knowledge base esistente."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"karray_knowledge_backup_{timestamp}.jsonl"
        
        if self.main_knowledge_file.exists():
            shutil.copy2(self.main_knowledge_file, backup_file)
            logger.info(f"📦 Backup creato: {backup_file}")
    
    async def _integrate_with_existing(self, new_documents: List[ExtractedDocument]):
        """Integra i nuovi documenti con quelli esistenti."""
        existing_documents = []
        
        # Carica documenti esistenti
        if self.main_knowledge_file.exists():
            existing_documents = await self._load_existing_documents()
        
        # Deduplica basata su content hash
        existing_hashes = {doc.get('file_hash') for doc in existing_documents if 'file_hash' in doc}
        
        new_unique_documents = []
        for doc in new_documents:
            if doc.file_hash not in existing_hashes:
                new_unique_documents.append(doc)
        
        # Combina tutti i documenti
        all_documents = existing_documents + [doc.__dict__ for doc in new_unique_documents]
        
        # Salva la knowledge base integrata
        await self._save_integrated_knowledge(all_documents)
        
        logger.info(f"🔄 Integrati {len(new_unique_documents)} nuovi documenti con {len(existing_documents)} esistenti")
    
    async def _replace_knowledge_base(self, documents: List[ExtractedDocument]):
        """Sostituisce completamente la knowledge base."""
        all_documents = [doc.__dict__ for doc in documents]
        await self._save_integrated_knowledge(all_documents)
        logger.info(f"🔄 Knowledge base sostituita con {len(documents)} documenti")
    
    async def _load_existing_documents(self) -> List[Dict[str, Any]]:
        """Carica i documenti esistenti dalla knowledge base."""
        documents = []
        
        try:
            with open(self.main_knowledge_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        doc = json.loads(line)
                        documents.append(doc)
        except Exception as e:
            logger.error(f"Errore caricando documenti esistenti: {e}")
        
        return documents
    
    async def _save_integrated_knowledge(self, documents: List[Dict[str, Any]]):
        """Salva la knowledge base integrata."""
        # Ordina per confidence score e timestamp
        documents.sort(key=lambda x: (
            x.get('confidence_score', 0),
            x.get('extraction_timestamp', '')
        ), reverse=True)
        
        # Salva in formato JSONL
        with open(self.main_knowledge_file, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\\n')
        
        logger.info(f"💾 Salvati {len(documents)} documenti nella knowledge base")
    
    def _analyze_categories(self, documents: List[ExtractedDocument]) -> Dict[str, int]:
        """Analizza la distribuzione delle categorie."""
        categories = {}
        for doc in documents:
            category = doc.category
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _analyze_product_coverage(self, documents: List[ExtractedDocument]) -> Dict[str, int]:
        """Analizza la copertura dei prodotti."""
        products = {}
        for doc in documents:
            for product in doc.product_tags:
                products[product] = products.get(product, 0) + 1
        return products
    
    def _analyze_quality(self, documents: List[ExtractedDocument]) -> Dict[str, float]:
        """Analizza la qualità dei documenti estratti."""
        if not documents:
            return {}
        
        confidence_scores = [doc.confidence_score for doc in documents]
        
        return {
            'avg_confidence': sum(confidence_scores) / len(confidence_scores),
            'min_confidence': min(confidence_scores),
            'max_confidence': max(confidence_scores),
            'high_quality_count': len([s for s in confidence_scores if s >= 0.8]),
            'medium_quality_count': len([s for s in confidence_scores if 0.6 <= s < 0.8]),
            'low_quality_count': len([s for s in confidence_scores if s < 0.6])
        }
    
    async def _generate_extraction_report(self) -> str:
        """Genera un report dettagliato dell'estrazione."""
        stats = self.extraction_stats
        
        report = f"""
📊 REPORT ESTRAZIONE K-ARRAY
{'=' * 50}

🕒 Timestamp: {stats['timestamp']}
⏱️  Tempo di estrazione: {stats['extraction_time']:.1f} secondi

📄 DOCUMENTI ESTRATTI: {stats['total_documents']}

📂 CATEGORIE:
{self._format_dict(stats['categories'])}

🏷️  PRODOTTI COPERTI:
{self._format_dict(stats['product_coverage'])}

⭐ QUALITÀ:
- Confidence media: {stats['quality_scores']['avg_confidence']:.2f}
- Documenti alta qualità (≥0.8): {stats['quality_scores']['high_quality_count']}
- Documenti media qualità (0.6-0.8): {stats['quality_scores']['medium_quality_count']}
- Documenti bassa qualità (<0.6): {stats['quality_scores']['low_quality_count']}

🔧 STATISTICHE EXTRACTOR:
- Pagine elaborate: {stats['extractor_stats']['total_pages']}
- PDF processati: {stats['extractor_stats']['pdfs_processed']}
- Excel processati: {stats['extractor_stats']['excel_processed']}
- Word processati: {stats['extractor_stats']['word_processed']}
- Errori: {stats['extractor_stats']['errors']}
- Duplicati saltati: {stats['extractor_stats']['duplicates_skipped']}

✅ ESTRAZIONE COMPLETATA CON SUCCESSO!
"""
        
        # Salva il report
        report_file = self.output_dir / f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report
    
    def _format_dict(self, d: Dict, max_items: int = 10) -> str:
        """Formatta un dizionario per il report."""
        items = sorted(d.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for key, value in items[:max_items]:
            lines.append(f"  - {key}: {value}")
        
        if len(items) > max_items:
            lines.append(f"  ... e altri {len(items) - max_items} elementi")
        
        return '\\n'.join(lines) if lines else "  Nessun elemento trovato"
    
    async def test_keyword_extraction(self, sample_text: str) -> Dict[str, Any]:
        """Testa il sistema di estrazione keywords su un testo campione."""
        extractor = KeywordExtractor()
        keywords, products, category = extractor.extract_keywords(sample_text)
        
        return {
            'text': sample_text[:200] + "..." if len(sample_text) > 200 else sample_text,
            'keywords': keywords,
            'products': products, 
            'category': category,
            'keyword_count': len(keywords),
            'product_count': len(products)
        }
    
    async def validate_extraction_quality(self) -> Dict[str, Any]:
        """Valida la qualità dell'estrazione effettuata."""
        if not self.main_knowledge_file.exists():
            return {'error': 'Knowledge base non trovata'}
        
        documents = await self._load_existing_documents()
        
        # Analisi qualità
        total_docs = len(documents)
        high_quality = len([d for d in documents if d.get('confidence_score', 0) >= 0.8])
        
        # Analisi keywords
        total_keywords = sum(len(d.get('keywords', [])) for d in documents)
        avg_keywords = total_keywords / total_docs if total_docs > 0 else 0
        
        # Analisi prodotti
        products_covered = set()
        for doc in documents:
            products_covered.update(doc.get('product_tags', []))
        
        return {
            'total_documents': total_docs,
            'high_quality_percentage': (high_quality / total_docs * 100) if total_docs > 0 else 0,
            'average_keywords_per_doc': avg_keywords,
            'unique_products_covered': len(products_covered),
            'products_list': sorted(list(products_covered))
        }

# Funzioni di utilità per l'esecuzione
async def run_extraction(incremental: bool = True):
    """Esegue l'estrazione completa."""
    manager = ExtractionManager()
    result = await manager.run_full_extraction(incremental=incremental)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

async def test_keywords(text: str):
    """Testa l'estrazione di keywords su un testo."""
    manager = ExtractionManager()
    result = await manager.test_keyword_extraction(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

async def validate_quality():
    """Valida la qualità dell'estrazione."""
    manager = ExtractionManager()
    result = await manager.validate_extraction_quality()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "extract":
            incremental = "--full" not in sys.argv
            asyncio.run(run_extraction(incremental))
        
        elif command == "test":
            test_text = " ".join(sys.argv[2:]) or "K-Framework 3 software for acoustical simulation"
            asyncio.run(test_keywords(test_text))
        
        elif command == "validate":
            asyncio.run(validate_quality())
        
        else:
            print("Uso: python extraction_manager.py [extract|test|validate]")
    else:
        print("🚀 Avvio estrazione completa...")
        asyncio.run(run_extraction())