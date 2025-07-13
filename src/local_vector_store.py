#!/usr/bin/env python3
"""
Local Vector Store for K-Array Chat System
File-based vector store compatible with Windows without external dependencies
"""

import json
import logging
import hashlib
import pickle
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class LocalVectorStore:
    """Local file-based vector store for Windows compatibility"""
    
    def __init__(self, 
                 store_directory: str = "./data/vector_store",
                 embedding_model: str = "all-mpnet-base-v2"):
        
        self.store_directory = Path(store_directory)
        self.store_directory.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        
        # File paths
        self.embeddings_file = self.store_directory / "embeddings.pkl"
        self.documents_file = self.store_directory / "documents.json"
        self.metadata_file = self.store_directory / "metadata.json"
        
        # In-memory storage
        self.embeddings = []
        self.documents = []
        self.metadata = []
        
        # Statistics
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'last_updated': None,
            'document_types': {}
        }
        
        self.setup_logging()
        self.initialize_components()
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def initialize_components(self):
        """Initialize embedding model and load existing data"""
        try:
            self.logger.info("Initializing Local Vector Store...")
            
            # Initialize SentenceTransformer for embeddings
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.logger.info(f"Loading embedding model: {self.embedding_model_name}")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
            else:
                self.logger.warning("SentenceTransformers not available. Using mock embeddings.")
                self.embedding_model = None
            
            # Load existing data
            self.load_data()
            
            self.update_stats()
            self.logger.info(f"Local vector store initialized with {self.stats['total_documents']} documents")
            
        except Exception as e:
            self.logger.error(f"Error initializing local vector store: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using SentenceTransformer or mock for testing"""
        if self.embedding_model is not None:
            embeddings = self.embedding_model.encode(texts, normalize_embeddings=True)
            return embeddings.astype(np.float32)
        else:
            # Mock embeddings for testing (random but consistent)
            np.random.seed(42)  # For reproducible results
            embeddings = np.random.rand(len(texts), 768).astype(np.float32)
            # Normalize for consistency
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            return embeddings / norms
    
    def create_document_id(self, source_path: str, content_type: str, index: int) -> str:
        """Create unique document ID"""
        base_name = Path(source_path).stem
        unique_string = f"{base_name}_{content_type}_{index}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def save_data(self):
        """Save data to disk"""
        try:
            # Save embeddings as pickle
            if self.embeddings:
                with open(self.embeddings_file, 'wb') as f:
                    pickle.dump(np.array(self.embeddings), f)
            
            # Save documents as JSON
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
            # Save metadata as JSON
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Data saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
    
    def load_data(self):
        """Load existing data from disk"""
        try:
            # Load embeddings
            if self.embeddings_file.exists():
                with open(self.embeddings_file, 'rb') as f:
                    embeddings_array = pickle.load(f)
                    self.embeddings = embeddings_array.tolist()
                self.logger.info(f"Loaded {len(self.embeddings)} embeddings")
            
            # Load documents
            if self.documents_file.exists():
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                self.logger.info(f"Loaded {len(self.documents)} documents")
            
            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self.logger.info(f"Loaded {len(self.metadata)} metadata entries")
            
        except Exception as e:
            self.logger.warning(f"Could not load existing data: {str(e)}")
            self.embeddings = []
            self.documents = []
            self.metadata = []
    
    def extract_specs_text(self, specs: Dict[str, Any]) -> str:
        """Extract text from specifications dictionary"""
        spec_texts = []
        for category, items in specs.items():
            if isinstance(items, dict):
                for key, value in items.items():
                    if isinstance(value, str):
                        spec_texts.append(f"{key}: {value}")
            elif isinstance(items, str):
                spec_texts.append(f"{category}: {items}")
        return " ".join(spec_texts)
    
    def process_json_file(self, json_path: str) -> List[Dict[str, Any]]:
        """Process a single JSON file and extract searchable content"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            processed_docs = []
            base_metadata = {
                'source_file': json_path,
                'source_url': data.get('url', ''),
                'document_type': 'k_array_json',
                'category': data.get('metadata', {}).get('category', 'unknown'),
                'subcategory': data.get('metadata', {}).get('subcategory', ''),
                'product_line': data.get('metadata', {}).get('product_line', ''),
                'model': data.get('metadata', {}).get('model', ''),
                'extraction_quality': data.get('extraction_quality', 'unknown'),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            
            # 1. Main searchable text
            if data.get('embedding_optimized', {}).get('searchable_text'):
                processed_docs.append({
                    'id': self.create_document_id(json_path, 'searchable', 0),
                    'content': data['embedding_optimized']['searchable_text'],
                    'metadata': {**base_metadata, 'content_type': 'searchable_text'},
                    'keywords': data.get('keywords', {}),
                    'source_attributions': data.get('source_attributions', [])
                })
            
            # 2. Semantic chunks
            semantic_chunks = data.get('embedding_optimized', {}).get('semantic_chunks', [])
            for i, chunk in enumerate(semantic_chunks):
                processed_docs.append({
                    'id': self.create_document_id(json_path, 'chunk', i),
                    'content': chunk,
                    'metadata': {**base_metadata, 'content_type': 'semantic_chunk', 'chunk_index': i},
                    'keywords': data.get('keywords', {}),
                    'source_attributions': data.get('source_attributions', [])
                })
            
            # 3. QA pairs
            qa_pairs = data.get('embedding_optimized', {}).get('qa_pairs', [])
            for i, qa in enumerate(qa_pairs):
                # Process question
                processed_docs.append({
                    'id': self.create_document_id(json_path, 'question', i),
                    'content': qa.get('question', qa.get('q', '')),
                    'metadata': {**base_metadata, 'content_type': 'question', 'qa_index': i},
                    'answer': qa.get('answer', qa.get('a', '')),
                    'qa_source': qa.get('source', ''),
                    'keywords': data.get('keywords', {})
                })
                
                # Process answer
                processed_docs.append({
                    'id': self.create_document_id(json_path, 'answer', i),
                    'content': qa.get('answer', qa.get('a', '')),
                    'metadata': {**base_metadata, 'content_type': 'answer', 'qa_index': i},
                    'question': qa.get('question', qa.get('q', '')),
                    'qa_source': qa.get('source', ''),
                    'keywords': data.get('keywords', {})
                })
            
            # 4. Technical specifications
            specs = data.get('product_specifications', {})
            if specs:
                specs_text = self.extract_specs_text(specs)
                if specs_text:
                    processed_docs.append({
                        'id': self.create_document_id(json_path, 'specs', 0),
                        'content': specs_text,
                        'metadata': {**base_metadata, 'content_type': 'technical_specs'},
                        'specifications': specs,
                        'keywords': data.get('keywords', {})
                    })
            
            self.logger.info(f"Processed {len(processed_docs)} documents from {json_path}")
            return processed_docs
            
        except Exception as e:
            self.logger.error(f"Error processing JSON file {json_path}: {str(e)}")
            return []
    
    def ingest_json_files(self, data_directory: str = "data") -> int:
        """Ingest all JSON files from data directory"""
        json_files = list(Path(data_directory).glob("extracted_data_*.json"))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {data_directory}")
            return 0
        
        self.logger.info(f"Found {len(json_files)} JSON files to process")
        
        new_documents = []
        new_metadata = []
        new_embeddings = []
        
        for json_file in json_files:
            processed_docs = self.process_json_file(str(json_file))
            
            if processed_docs:
                # Extract content for embedding
                contents = [doc['content'] for doc in processed_docs]
                
                # Generate embeddings
                embeddings = self.generate_embeddings(contents)
                
                # Store data
                for doc, embedding in zip(processed_docs, embeddings):
                    new_documents.append({
                        'id': doc['id'],
                        'content': doc['content']
                    })
                    new_metadata.append(doc['metadata'])
                    new_embeddings.append(embedding.tolist())
        
        # Add to existing data
        self.documents.extend(new_documents)
        self.metadata.extend(new_metadata)
        self.embeddings.extend(new_embeddings)
        
        # Save to disk
        self.save_data()
        
        ingested_count = len(new_documents)
        self.logger.info(f"Successfully ingested {ingested_count} documents")
        self.update_stats()
        
        return ingested_count
    
    def update_stats(self):
        """Update collection statistics"""
        try:
            self.stats.update({
                'total_documents': len(self.documents),
                'total_chunks': len([m for m in self.metadata if m.get('content_type') == 'semantic_chunk']),
                'last_updated': datetime.now().isoformat()
            })
        except Exception as e:
            self.logger.warning(f"Could not update stats: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        self.update_stats()
        return self.stats
    
    def search(self, 
               query: str, 
               top_k: int = 5, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents with optional filters"""
        try:
            if not self.documents:
                return []
            
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Calculate similarities
            if SKLEARN_AVAILABLE:
                # Use sklearn for cosine similarity
                embeddings_array = np.array(self.embeddings)
                similarities = cosine_similarity([query_embedding], embeddings_array)[0]
            else:
                # Manual cosine similarity calculation
                similarities = []
                for doc_embedding in self.embeddings:
                    doc_embedding = np.array(doc_embedding)
                    similarity = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                    similarities.append(similarity)
                similarities = np.array(similarities)
            
            # Get top k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Apply filters if provided
            if filters:
                filtered_indices = []
                for idx in top_indices:
                    metadata = self.metadata[idx]
                    include = True
                    for key, value in filters.items():
                        if key in metadata:
                            if isinstance(value, list):
                                if metadata[key] not in value:
                                    include = False
                                    break
                            else:
                                if metadata[key] != value:
                                    include = False
                                    break
                    if include:
                        filtered_indices.append(idx)
                top_indices = filtered_indices[:top_k]
            
            # Format results
            results = []
            for idx in top_indices:
                results.append({
                    'id': self.documents[idx]['id'],
                    'content': self.documents[idx]['content'],
                    'score': float(similarities[idx]),
                    'metadata': self.metadata[idx]
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during search: {str(e)}")
            return []
    
    def hybrid_search(self, 
                     query: str, 
                     top_k: int = 5, 
                     filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Hybrid search combining semantic and keyword search"""
        # For now, implement as enhanced semantic search
        return self.search(query, top_k, filters)


if __name__ == "__main__":
    # Test the local vector store
    try:
        vector_store = LocalVectorStore()
        print(f"✅ Local vector store initialized successfully")
        
        # Test search (will be empty initially)
        results = vector_store.search("test query", top_k=1)
        print(f"✅ Search test completed - found {len(results)} results")
        
        # Test stats
        stats = vector_store.get_stats()
        print(f"✅ Stats: {stats}")
        
    except Exception as e:
        print(f"❌ Error testing local vector store: {e}")