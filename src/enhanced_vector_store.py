#!/usr/bin/env python3
"""
Enhanced Vector Store for K-Array Chat System using Milvus
High-performance vector store with advanced search capabilities
"""

import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
from src.dynamic_config import dynamic_config

from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class EnhancedVectorStore:
    """Enhanced vector store using Milvus for superior performance"""
    
    def __init__(self, 
                 collection_name: str = None,
                 embedding_model: str = None,
                 host: str = None,
                 port: str = None):
        
        # Use dynamic configuration with fallbacks
        config = dynamic_config.vector_store_config
        self.collection_name = collection_name or config.collection_name
        self.embedding_model_name = embedding_model or config.embedding_model
        self.embedding_model = None
        self.collection = None
        self.host = host or config.host
        self.port = port or config.port
        
        # Statistics tracking
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
        """Initialize Milvus connection and embedding model"""
        try:
            self.logger.info("Initializing Enhanced Vector Store with Milvus...")
            
            # Initialize SentenceTransformer for embeddings
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.logger.info(f"Loading embedding model: {self.embedding_model_name}")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
            else:
                self.logger.warning("SentenceTransformers not available. Using mock embeddings for testing.")
                self.embedding_model = None
            
            # Connect to Milvus
            self.logger.info(f"Connecting to Milvus at {self.host}:{self.port}")
            connections.connect("default", host=self.host, port=self.port)
            
            # Create collection if not exists
            self._create_collection()
            
            # Load collection
            self.collection.load()
            
            self.update_stats()
            self.logger.info(f"Enhanced vector store initialized with {self.stats['total_documents']} documents")
            
        except Exception as e:
            self.logger.error(f"Error initializing enhanced vector store: {str(e)}")
            raise
    
    def _create_collection(self):
        """Create Milvus collection with optimized schema"""
        try:
            # Check if collection exists
            if utility.has_collection(self.collection_name):
                self.logger.info(f"Collection {self.collection_name} already exists")
                self.collection = Collection(self.collection_name)
                return
            
            # Define schema with all necessary fields
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),  # mpnet dimension
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="subcategory", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="product_line", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="model", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="keywords_primary", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="keywords_technical", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="extraction_quality", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=50)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="K-Array product knowledge base with enhanced metadata"
            )
            
            # Create collection
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
                using='default'
            )
            
            self.logger.info(f"Created collection {self.collection_name}")
            
            # Create optimized index for quality retrieval
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "IP",  # Inner Product for normalized vectors
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            self.logger.info("Created optimized vector index")
            
        except Exception as e:
            self.logger.error(f"Error creating collection: {str(e)}")
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
        
        all_data = {
            'ids': [],
            'embeddings': [],
            'contents': [],
            'source_files': [],
            'source_urls': [],
            'document_types': [],
            'categories': [],
            'subcategories': [],
            'product_lines': [],
            'models': [],
            'content_types': [],
            'keywords_primary': [],
            'keywords_technical': [],
            'extraction_qualities': [],
            'timestamps': []
        }
        
        for json_file in json_files:
            processed_docs = self.process_json_file(str(json_file))
            
            if processed_docs:
                # Extract content for embedding
                contents = [doc['content'] for doc in processed_docs]
                
                # Generate embeddings
                embeddings = self.generate_embeddings(contents)
                
                # Prepare data for Milvus
                for doc, embedding in zip(processed_docs, embeddings):
                    keywords = doc.get('keywords', [])
                    if isinstance(keywords, list):
                        keywords_primary = keywords
                        keywords_technical = []
                    elif isinstance(keywords, dict):
                        keywords_primary = keywords.get('primary', [])
                        keywords_technical = keywords.get('technical', [])
                    else:
                        keywords_primary = []
                        keywords_technical = []
                    
                    all_data['ids'].append(doc['id'])
                    all_data['embeddings'].append(embedding.tolist())
                    all_data['contents'].append(doc['content'])
                    all_data['source_files'].append(doc['metadata']['source_file'])
                    all_data['source_urls'].append(doc['metadata']['source_url'])
                    all_data['document_types'].append(doc['metadata']['document_type'])
                    all_data['categories'].append(doc['metadata']['category'])
                    all_data['subcategories'].append(doc['metadata']['subcategory'])
                    all_data['product_lines'].append(doc['metadata']['product_line'])
                    all_data['models'].append(doc['metadata']['model'])
                    all_data['content_types'].append(doc['metadata']['content_type'])
                    all_data['keywords_primary'].append(json.dumps(keywords_primary))
                    all_data['keywords_technical'].append(json.dumps(keywords_technical))
                    all_data['extraction_qualities'].append(doc['metadata']['extraction_quality'])
                    all_data['timestamps'].append(doc['metadata']['timestamp'])
        
        # Batch insert to Milvus
        if all_data['ids']:
            try:
                # Prepare data in correct format
                entities = [
                    all_data['ids'],
                    all_data['embeddings'],
                    all_data['contents'],
                    all_data['source_files'],
                    all_data['source_urls'],
                    all_data['document_types'],
                    all_data['categories'],
                    all_data['subcategories'],
                    all_data['product_lines'],
                    all_data['models'],
                    all_data['content_types'],
                    all_data['keywords_primary'],
                    all_data['keywords_technical'],
                    all_data['extraction_qualities'],
                    all_data['timestamps']
                ]
                
                self.collection.insert(entities)
                self.collection.flush()
                
                ingested_count = len(all_data['ids'])
                self.logger.info(f"Successfully ingested {ingested_count} documents to Milvus")
                self.update_stats()
                
                return ingested_count
                
            except Exception as e:
                self.logger.error(f"Error inserting documents to Milvus: {str(e)}")
                return 0
        
        return 0
    
    def update_stats(self):
        """Update collection statistics"""
        try:
            if self.collection is not None:
                count = self.collection.num_entities
                self.stats.update({
                    'total_documents': count,
                    'last_updated': datetime.now().isoformat()
                })
            else:
                self.stats.update({
                    'total_documents': 0,
                    'last_updated': datetime.now().isoformat()
                })
        except Exception as e:
            self.logger.warning(f"Could not update stats: {str(e)}")
            self.stats.update({
                'total_documents': 0,
                'last_updated': datetime.now().isoformat()
            })
    
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
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0].tolist()
            
            # Define search parameters
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }
            
            # Build filter expression if provided
            filter_expr = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_conditions.append(f'{key} == "{value}"')
                    elif isinstance(value, list):
                        value_str = '", "'.join(value)
                        filter_conditions.append(f'{key} in ["{value_str}"]')
                if filter_conditions:
                    filter_expr = " and ".join(filter_conditions)
            
            # Perform search
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=["content", "source_file", "source_url", "category", 
                              "product_line", "model", "content_type", "keywords_primary"]
            )
            
            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        'id': hit.id,
                        'content': hit.entity.get('content', ''),
                        'score': hit.score,
                        'metadata': {
                            'source_file': hit.entity.get('source_file', ''),
                            'source_url': hit.entity.get('source_url', ''),
                            'category': hit.entity.get('category', ''),
                            'product_line': hit.entity.get('product_line', ''),
                            'model': hit.entity.get('model', ''),
                            'content_type': hit.entity.get('content_type', ''),
                            'keywords_primary': hit.entity.get('keywords_primary', '')
                        }
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error during search: {str(e)}")
            return []
    
    def hybrid_search(self, 
                     query: str, 
                     top_k: int = 5, 
                     filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Hybrid search combining semantic and keyword search"""
        # For now, implement as enhanced semantic search
        # TODO: Add BM25 component in Phase 2
        return self.search(query, top_k, filters)


if __name__ == "__main__":
    # Test the enhanced vector store
    try:
        vector_store = EnhancedVectorStore()
        print(f"✅ Enhanced vector store initialized successfully")
        
        # Test search (will be empty initially)
        results = vector_store.search("test query", top_k=1)
        print(f"✅ Search test completed - found {len(results)} results")
        
        # Test stats
        stats = vector_store.get_stats()
        print(f"✅ Stats: {stats}")
        
    except Exception as e:
        print(f"❌ Error testing enhanced vector store: {e}")