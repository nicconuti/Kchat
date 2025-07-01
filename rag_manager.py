"""
RAG Manager for K-Chat system.
Handles document ingestion, processing, and integration with the chat system.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json
import shutil
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths for imports
sys.path.append(str(Path(__file__).parent / "knowledge_pipeline"))
sys.path.append(str(Path(__file__).parent / "karray_rag"))

class DocumentProcessor:
    """Handles document processing and ingestion into the RAG system."""
    
    def __init__(self, 
                 output_dir: str = "backend_data/knowledge_base",
                 karray_rag_dir: str = "karray_rag/data"):
        self.output_dir = Path(output_dir)
        self.karray_rag_dir = Path(karray_rag_dir)
        self.processed_docs_file = self.output_dir / "processed_documents.json"
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.karray_rag_dir.mkdir(parents=True, exist_ok=True)
        
        # Load processed documents registry
        self.processed_docs = self._load_processed_registry()
    
    def _load_processed_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load registry of already processed documents."""
        if self.processed_docs_file.exists():
            try:
                with open(self.processed_docs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load processed documents registry: {e}")
        return {}
    
    def _save_processed_registry(self):
        """Save registry of processed documents."""
        try:
            with open(self.processed_docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_docs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save processed documents registry: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash for file change detection."""
        import hashlib
        
        hash_obj = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Could not generate hash for {file_path}: {e}")
            return ""
    
    def process_document(self, file_path: Union[str, Path], 
                        category: Optional[str] = None,
                        force_reprocess: bool = False) -> bool:
        """
        Process a single document and add it to the knowledge base.
        
        Args:
            file_path: Path to the document to process
            category: Document category (product_info, tech_assistance, etc.)
            force_reprocess: Force reprocessing even if document already exists
            
        Returns:
            True if successfully processed, False otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        # Check if already processed
        file_key = str(file_path.absolute())
        current_hash = self._get_file_hash(file_path)
        
        if not force_reprocess and file_key in self.processed_docs:
            stored_hash = self.processed_docs[file_key].get('hash', '')
            if stored_hash == current_hash:
                logger.info(f"Document already processed: {file_path.name}")
                return True
        
        logger.info(f"Processing document: {file_path.name}")
        
        try:
            # Use knowledge pipeline for processing
            success = self._process_with_knowledge_pipeline(file_path, category)
            
            if success:
                # Update registry
                self.processed_docs[file_key] = {
                    'hash': current_hash,
                    'processed_at': datetime.now().isoformat(),
                    'file_name': file_path.name,
                    'category': category or 'unclassified',
                    'file_size': file_path.stat().st_size
                }
                self._save_processed_registry()
                logger.info(f"Successfully processed: {file_path.name}")
                return True
            else:
                logger.error(f"Failed to process: {file_path.name}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            return False
    
    def _process_with_knowledge_pipeline(self, file_path: Path, category: Optional[str]) -> bool:
        """Process document using the knowledge pipeline."""
        try:
            # Import knowledge pipeline components
            from knowledge_pipeline.core import KnowledgePipeline
            from knowledge_pipeline.config import CONFIG
            
            # Configure output to our knowledge base
            output_file = self.output_dir / f"processed_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            
            # Initialize pipeline
            pipeline = KnowledgePipeline(
                input_dir=str(file_path.parent),
                output_file=str(output_file),
                config=CONFIG
            )
            
            # Process single file
            success = pipeline.process_single_file(file_path, category)
            
            if success and output_file.exists():
                # Integrate with K-Array RAG system
                self._integrate_with_karray_rag(output_file)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Knowledge pipeline processing failed: {e}")
            return False
    
    def _integrate_with_karray_rag(self, processed_file: Path):
        """Integrate processed documents with K-Array RAG system."""
        try:
            # Load processed documents
            documents = []
            with open(processed_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        documents.append(json.loads(line))
            
            if not documents:
                return
            
            # Append to main K-Array knowledge base
            karray_knowledge_base = self.karray_rag_dir / "embedded_karray_documents.jsonl"
            
            # Create backup if file exists
            if karray_knowledge_base.exists():
                backup_file = karray_knowledge_base.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl')
                shutil.copy2(karray_knowledge_base, backup_file)
                logger.info(f"Created backup: {backup_file.name}")
            
            # Append new documents
            with open(karray_knowledge_base, 'a', encoding='utf-8') as f:
                for doc in documents:
                    f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            
            logger.info(f"Integrated {len(documents)} documents into K-Array RAG system")
            
        except Exception as e:
            logger.error(f"Failed to integrate with K-Array RAG: {e}")
    
    def process_directory(self, directory: Union[str, Path], 
                         recursive: bool = True,
                         supported_extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process all supported documents in a directory.
        
        Args:
            directory: Directory path to process
            recursive: Process subdirectories
            supported_extensions: List of supported file extensions
            
        Returns:
            Processing summary with statistics
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return {"success": False, "error": "Directory not found"}
        
        if supported_extensions is None:
            supported_extensions = ['.pdf', '.docx', '.xlsx', '.csv', '.json', '.txt', '.html', '.xml']
        
        # Find files to process
        pattern = "**/*" if recursive else "*"
        files_to_process = []
        
        for ext in supported_extensions:
            files_to_process.extend(directory.glob(f"{pattern}{ext}"))
        
        if not files_to_process:
            logger.warning(f"No supported files found in {directory}")
            return {"success": True, "processed": 0, "failed": 0, "files": []}
        
        logger.info(f"Found {len(files_to_process)} files to process in {directory}")
        
        # Process files
        processed_count = 0
        failed_count = 0
        processed_files = []
        
        for file_path in files_to_process:
            try:
                # Determine category based on directory structure or filename
                category = self._determine_category(file_path)
                
                success = self.process_document(file_path, category)
                
                if success:
                    processed_count += 1
                    processed_files.append({
                        "file": str(file_path),
                        "category": category,
                        "status": "success"
                    })
                else:
                    failed_count += 1
                    processed_files.append({
                        "file": str(file_path),
                        "category": category,
                        "status": "failed"
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                failed_count += 1
                processed_files.append({
                    "file": str(file_path),
                    "category": "unknown",
                    "status": "error",
                    "error": str(e)
                })
        
        summary = {
            "success": True,
            "total_found": len(files_to_process),
            "processed": processed_count,
            "failed": failed_count,
            "files": processed_files
        }
        
        logger.info(f"Processing complete: {processed_count} processed, {failed_count} failed")
        return summary
    
    def _determine_category(self, file_path: Path) -> str:
        """Determine document category based on path and filename."""
        path_parts = file_path.parts
        filename = file_path.name.lower()
        
        # Category mapping based on common patterns
        if any(part in ['manual', 'manuals', 'guide', 'guides', 'documentation'] for part in path_parts):
            return 'product_guide'
        elif any(part in ['price', 'prices', 'pricing', 'quote', 'quotes', 'cost'] for part in path_parts):
            return 'product_price'
        elif any(part in ['support', 'help', 'troubleshoot', 'tech'] for part in path_parts):
            return 'tech_assistance'
        elif any(part in ['software', 'app', 'application', 'program'] for part in path_parts):
            return 'software_assistance'
        elif any(keyword in filename for keyword in ['manual', 'guide', 'instruction']):
            return 'product_guide'
        elif any(keyword in filename for keyword in ['price', 'cost', 'quote', 'rate']):
            return 'product_price'
        elif any(keyword in filename for keyword in ['support', 'help', 'troubleshoot', 'fix']):
            return 'tech_assistance'
        else:
            return 'unclassified'
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents."""
        if not self.processed_docs:
            return {"total_processed": 0, "categories": {}, "recent_files": []}
        
        categories = {}
        recent_files = []
        
        for file_path, info in self.processed_docs.items():
            category = info.get('category', 'unclassified')
            categories[category] = categories.get(category, 0) + 1
            
            recent_files.append({
                "file": info.get('file_name', Path(file_path).name),
                "processed_at": info.get('processed_at'),
                "category": category,
                "size": info.get('file_size', 0)
            })
        
        # Sort by processing time (most recent first)
        recent_files.sort(key=lambda x: x['processed_at'], reverse=True)
        
        return {
            "total_processed": len(self.processed_docs),
            "categories": categories,
            "recent_files": recent_files[:10]  # Last 10 files
        }

class RAGManager:
    """Main RAG system manager for document operations and web refresh."""
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.web_refresh_log = Path("logs/web_refresh.log")
        self.web_refresh_log.parent.mkdir(parents=True, exist_ok=True)
    
    def add_document(self, file_path: Union[str, Path], 
                    category: Optional[str] = None) -> bool:
        """Add a single document to the knowledge base."""
        return self.doc_processor.process_document(file_path, category)
    
    def add_documents_from_directory(self, directory: Union[str, Path], 
                                   recursive: bool = True) -> Dict[str, Any]:
        """Add all supported documents from a directory."""
        return self.doc_processor.process_directory(directory, recursive)
    
    def refresh_web_content(self) -> bool:
        """Refresh web content from K-Array website."""
        try:
            # Import and run K-Array web scraping
            sys.path.append(str(Path(__file__).parent / "karray_rag"))
            from karray_rag_pipeline import main as run_web_scraping
            
            logger.info("Starting K-Array web content refresh...")
            
            # Log refresh attempt
            with open(self.web_refresh_log, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()}: Starting web refresh\n")
            
            # Run web scraping and processing
            run_web_scraping()
            
            # Log success
            with open(self.web_refresh_log, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()}: Web refresh completed successfully\n")
            
            logger.info("K-Array web content refresh completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Web refresh failed: {e}"
            logger.error(error_msg)
            
            # Log error
            with open(self.web_refresh_log, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()}: ERROR - {error_msg}\n")
            
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive RAG system status."""
        # Document processing stats
        doc_stats = self.doc_processor.get_processing_stats()
        
        # K-Array knowledge base stats
        karray_kb_path = Path("karray_rag/data/embedded_karray_documents.jsonl")
        karray_doc_count = 0
        if karray_kb_path.exists():
            with open(karray_kb_path, 'r', encoding='utf-8') as f:
                karray_doc_count = sum(1 for line in f if line.strip())
        
        # Web refresh status
        last_web_refresh = "Never"
        if self.web_refresh_log.exists():
            try:
                with open(self.web_refresh_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if "completed successfully" in last_line:
                            last_web_refresh = last_line.split(":")[0]
            except Exception:
                pass
        
        return {
            "document_processing": doc_stats,
            "karray_knowledge_base": {
                "total_documents": karray_doc_count,
                "file_path": str(karray_kb_path),
                "exists": karray_kb_path.exists()
            },
            "web_content": {
                "last_refresh": last_web_refresh,
                "log_file": str(self.web_refresh_log)
            },
            "system_health": {
                "knowledge_pipeline_available": self._check_knowledge_pipeline(),
                "karray_rag_available": self._check_karray_rag(),
                "embedding_models_available": self._check_embedding_models()
            }
        }
    
    def _check_knowledge_pipeline(self) -> bool:
        """Check if knowledge pipeline is available."""
        try:
            from knowledge_pipeline.core import KnowledgePipeline
            return True
        except ImportError:
            return False
    
    def _check_karray_rag(self) -> bool:
        """Check if K-Array RAG system is available."""
        try:
            from query_rag import EnhancedRetriever
            return True
        except ImportError:
            return False
    
    def _check_embedding_models(self) -> bool:
        """Check if embedding models are available."""
        try:
            from sentence_transformers import SentenceTransformer
            # Try to load a basic model
            SentenceTransformer('all-MiniLM-L6-v2')
            return True
        except Exception:
            return False

# CLI interface
def main():
    """Command line interface for RAG management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Manager for K-Chat")
    parser.add_argument("command", choices=["add-file", "add-dir", "refresh-web", "status"],
                       help="Command to execute")
    parser.add_argument("--path", help="File or directory path for add commands")
    parser.add_argument("--category", help="Document category")
    parser.add_argument("--recursive", action="store_true", help="Process directories recursively")
    
    args = parser.parse_args()
    
    rag_manager = RAGManager()
    
    if args.command == "add-file":
        if not args.path:
            print("Error: --path required for add-file command")
            return
        
        success = rag_manager.add_document(args.path, args.category)
        print(f"Document processing: {'SUCCESS' if success else 'FAILED'}")
    
    elif args.command == "add-dir":
        if not args.path:
            print("Error: --path required for add-dir command")
            return
        
        result = rag_manager.add_documents_from_directory(args.path, args.recursive)
        print(f"Directory processing: {result['processed']} processed, {result['failed']} failed")
    
    elif args.command == "refresh-web":
        success = rag_manager.refresh_web_content()
        print(f"Web refresh: {'SUCCESS' if success else 'FAILED'}")
    
    elif args.command == "status":
        status = rag_manager.get_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()