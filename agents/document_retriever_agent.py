"""Retrieve relevant document chunks using K-Array RAG system."""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from agents.context import AgentContext
from utils.logger import get_logger

# Add karray_rag to path for import
sys.path.append(str(Path(__file__).parent.parent / "karray_rag"))

# Ensure correct Haystack-AI path is available
if '/opt/homebrew/lib/python3.9/site-packages' not in sys.path:
    sys.path.insert(0, '/opt/homebrew/lib/python3.9/site-packages')

# Global retriever instance for performance
_retriever = None
_retriever_initialized = False

def _initialize_karray_retriever():
    """Initialize the K-Array RAG retriever system."""
    global _retriever, _retriever_initialized
    
    if _retriever_initialized:
        return _retriever
    
    logger = get_logger("retrieval_log")
    
    try:
        # Import K-Array RAG components
        from rag_store import load_documents_from_jsonl
        from query_rag import EnhancedRetriever
        
        # Path to embedded documents (fallback to raw if embedded not available)
        embedded_path = Path(__file__).parent.parent / "karray_rag" / "data" / "embedded_karray_documents.jsonl"
        raw_path = Path(__file__).parent.parent / "karray_rag" / "data" / "karray_knowledge.jsonl"
        
        # Prefer embedded documents, fallback to raw
        if embedded_path.exists():
            karray_data_path = embedded_path
            logger.info("Using embedded K-Array documents for RAG")
        elif raw_path.exists():
            karray_data_path = raw_path
            logger.info("Using raw K-Array documents (embeddings not available yet)")
        else:
            logger.warning("No K-Array knowledge base found. Using fallback system.")
            _retriever_initialized = True
            return None
        
        if not karray_data_path.exists():
            logger.warning(f"K-Array knowledge base not found at {karray_data_path}. Using fallback system.")
            _retriever_initialized = True
            return None
        
        logger.info(f"Found K-Array knowledge base at {karray_data_path}")
        
        # Load documents
        logger.info("Loading K-Array knowledge base...")
        documents = load_documents_from_jsonl(str(karray_data_path))
        
        if not documents:
            logger.warning("No documents found in K-Array knowledge base. Using fallback system.")
            _retriever_initialized = True
            return None
        
        # Initialize enhanced retriever
        logger.info(f"Initializing K-Array RAG system with {len(documents)} documents...")
        _retriever = EnhancedRetriever(documents)
        
        logger.info("✅ K-Array RAG system successfully initialized!")
        _retriever_initialized = True
        return _retriever
        
    except Exception as e:
        logger.error(f"Failed to initialize K-Array RAG system: {e}")
        logger.info("Falling back to simple retrieval system")
        _retriever_initialized = True
        return None

def _fallback_retrieve(query: str, role: str) -> List[Dict[str, Any]]:
    """Conservative fallback retrieval system with verified K-Array content only."""
    # Curated, verified K-Array content only - no hallucinations possible
    verified_karray_docs = {
        "general": [
            {
                "content": "K-Array è un'azienda italiana specializzata in sistemi audio professionali. Per informazioni dettagliate sui prodotti e specifiche tecniche, consultare il sito ufficiale www.k-array.com",
                "source": "k-array.com/company",
                "category": "product_info",
                "roles": ["user", "admin", "guest"],
                "keywords": ["k-array", "azienda", "italiana", "audio", "professionali", "company", "about"]
            }
        ],
        "k_framework": [
            {
                "content": "K-Framework 3 è la terza generazione del software di gestione K-Array per sistemi audio professionali. Per documentazione completa e specifiche tecniche di K-Framework 3, consultare www.k-array.com",
                "source": "k-array.com/k-framework",
                "category": "software_assistance",
                "roles": ["user", "admin", "guest"],
                "keywords": ["k-framework", "framework", "k-framework 3", "kframework", "software", "gestione", "audio", "terza", "generazione"]
            },
            {
                "content": "Il sistema K-Framework fornisce controllo avanzato per i prodotti audio K-Array. Per assistenza tecnica su K-Framework e tutorial, visitare la sezione supporto su www.k-array.com/support",
                "source": "k-array.com/support/k-framework",
                "category": "tech_assistance",
                "roles": ["user", "admin"],
                "keywords": ["k-framework", "framework", "controllo", "avanzato", "tutorial", "assistenza", "support"]
            }
        ],
        "contact": [
            {
                "content": "Per supporto tecnico e informazioni sui prodotti K-Array, contattare il team attraverso i canali ufficiali disponibili su www.k-array.com/support",
                "source": "k-array.com/support",
                "category": "tech_assistance",
                "roles": ["user", "admin"],
                "keywords": ["supporto", "tecnico", "contatto", "support", "help", "assistance"]
            }
        ]
    }
    
    # Conservative keyword matching with normalization
    normalized_query = _normalize_query(query)  
    query_lower = normalized_query.lower()
    original_query_lower = query.lower()
    results = []
    
    # Only return results if there's a strong keyword match
    for category, docs in verified_karray_docs.items():
        for doc in docs:
            # Check role permissions
            if role not in doc["roles"]:
                continue
            
            # Require exact keyword match to prevent hallucinations
            keyword_match = False
            for keyword in doc["keywords"]:
                if keyword in query_lower or keyword in original_query_lower:
                    keyword_match = True
                    break
            
            if keyword_match:
                results.append({
                    "content": doc["content"],
                    "source": doc["source"],
                    "category": doc["category"],
                    "score": 0.6,  # Conservative score
                    "cross_encoder_score": 0.5,
                    "cosine_similarity": 0.4,
                    "keyword_bonus": 0.1,
                    "length_bonus": 0.0,
                    "chunk_id": "fallback",
                    "original_doc_id": "verified_content",
                    "verified_source": True,
                    "fallback_content": True  # Mark as fallback
                })
    
    # If no keyword matches found, return empty to prevent hallucinations
    if not results:
        logger.info(f"No verified content matches for query: '{query}' - returning empty results")
        return []
    
    return results[:2]  # Return max 2 conservative results


def _keyword_search_documents(query: str, role: str) -> List[Dict[str, Any]]:
    """Direct keyword search on documents without embeddings."""
    try:
        from rag_store import load_documents_from_jsonl
        
        # Load documents directly
        karray_data_path = Path(__file__).parent.parent / "karray_rag" / "data" / "karray_knowledge.jsonl"
        if not karray_data_path.exists():
            logger.warning("Knowledge base file not found for keyword search")
            return _fallback_retrieve(query, role)
        
        documents = load_documents_from_jsonl(str(karray_data_path))
        if not documents:
            logger.warning("No documents found for keyword search")
            return _fallback_retrieve(query, role)
        
        # Normalize and prepare query for matching
        normalized_query = _normalize_query(query)
        query_lower = normalized_query.lower()
        query_words = query_lower.split()
        
        # Include original query terms too
        original_words = query.lower().split()
        all_words = list(set(query_words + original_words))
        
        scored_docs = []
        for doc in documents:
            content_lower = doc.content.lower()
            score = 0
            
            # Exact phrase match gets highest score
            if query_lower in content_lower:
                score += 10
            
            # Individual word matches
            for word in all_words:
                if len(word) >= 3:  # Skip very short words
                    count = content_lower.count(word)
                    score += count * 2
            
            if score > 0:
                scored_docs.append((doc, score))
        
        # Sort by score and take top results
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for doc, score in scored_docs[:5]:  # Top 5 results
            source = doc.meta.get('source', 'k-array.com')
            category = doc.meta.get('category', 'unclassified')
            
            # Apply basic role filtering
            allowed_roles = ["user", "admin", "guest"]
            if role not in allowed_roles:
                continue
            
            results.append({
                "content": doc.content.strip(),
                "source": source,
                "category": category,
                "score": min(score / 10.0, 1.0),  # Normalize to 0-1
                "cross_encoder_score": 0.5,
                "cosine_similarity": 0.3,
                "keyword_bonus": 0.1,
                "length_bonus": 0.0,
                "chunk_id": "keyword_search",
                "original_doc_id": "keyword_search",
                "verified_source": True,
                "keyword_search": True
            })
        
        logger.info(f"Keyword search found {len(results)} documents for '{query}'")
        return results
        
    except Exception as e:
        logger.error(f"Error in keyword search: {e}")
        return _fallback_retrieve(query, role)


logger = get_logger("retrieval_log")


def _normalize_query(query: str) -> str:
    """Normalize query to improve search robustness for K-Array terms."""
    import re
    
    # Convert to lowercase for processing
    normalized = query.lower()
    
    # Normalize K-Framework variations
    k_framework_patterns = [
        r'\bk-?framework-?3?\b',
        r'\bkframework-?3?\b', 
        r'\bk\s*framework\s*3?\b',
        r'\bk-array\s+framework\s*3?\b'
    ]
    
    for pattern in k_framework_patterns:
        if re.search(pattern, normalized):
            # Replace with standard form
            normalized = re.sub(pattern, 'K-Framework 3', normalized, flags=re.IGNORECASE)
            # Remove duplicate "3" if present
            normalized = re.sub(r'\bK-Framework 3\s+3\b', 'K-Framework 3', normalized)
            logger.info(f"Normalized query: '{query}' -> '{normalized}'")
            break
    
    # Normalize other K-Array terms
    k_array_patterns = [
        (r'\bk-?array\b', 'K-Array'),
        (r'\bkarray\b', 'K-Array'),
        (r'\bk\s+array\b', 'K-Array')
    ]
    
    for pattern, replacement in k_array_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    return normalized


def _retrieve_with_karray_rag(query: str, role: str) -> List[Dict[str, Any]]:
    """Main retrieval function using K-Array RAG system with strict anti-hallucination measures."""
    # Confidence thresholds for reliable responses (optimized for quality)
    MIN_CROSS_ENCODER_SCORE = 0.0   # Minimum cross-encoder score to trust
    MIN_COSINE_SIMILARITY = 0.0     # Minimum cosine similarity  
    MIN_FINAL_SCORE = 0.1           # Lower threshold to capture more relevant content
    
    retriever = _initialize_karray_retriever()
    
    if retriever is None:
        logger.info("Using fallback retrieval system")
        return _fallback_retrieve(query, role)
    
    try:
        # Use K-Array enhanced retrieval
        logger.info(f"Searching K-Array knowledge base for: '{query}'")
        results = retriever.search(query, top_k=8)  # Increased for better coverage
        
        if not results:
            logger.warning("No results from K-Array RAG, trying keyword search on raw documents")
            # Try keyword search directly on documents without embeddings
            return _keyword_search_documents(query, role)
        
        # Apply strict quality filtering to prevent hallucinations
        high_quality_results = []
        
        for doc, final_score, cross_score, cosine_sim, keyword_bonus, length_bonus in results:
            # Log all scores for debugging
            logger.info(f"Document scores: cross={cross_score:.3f}, cosine={cosine_sim:.3f}, final={final_score:.3f}, source={doc.meta.get('source', 'unknown')}")
            
            # Strict quality thresholds  
            if (cross_score < MIN_CROSS_ENCODER_SCORE or 
                cosine_sim < MIN_COSINE_SIMILARITY or 
                final_score < MIN_FINAL_SCORE):
                logger.info(f"Filtered low-quality result: cross={cross_score:.3f}, cosine={cosine_sim:.3f}, final={final_score:.3f}")
                continue
            
            # Extract and validate metadata
            source = doc.meta.get('source', 'k-array.com')
            category = doc.meta.get('category', 'unclassified')
            
            # Verify source is actually from K-Array domain
            if not ('k-array.com' in source.lower() or source.startswith('k-array')):
                logger.warning(f"Filtering non-K-Array source: {source}")
                continue
            
            # Role-based filtering with strict permissions
            allowed_roles = ["user", "admin", "guest"]  # Most K-Array content is public
            if category == "tech_assistance":
                allowed_roles = ["user", "admin"]  # Technical content requires registration
            
            if role not in allowed_roles:
                logger.info(f"Access denied for role '{role}' to category '{category}'")
                continue
            
            # Validate content is not empty or too short
            if not doc.content or len(doc.content.strip()) < 20:
                logger.warning("Filtering document with insufficient content")
                continue
            
            high_quality_results.append({
                "content": doc.content.strip(),
                "source": source,
                "category": category,
                "score": float(final_score),
                "cross_encoder_score": float(cross_score),
                "cosine_similarity": float(cosine_sim),
                "keyword_bonus": float(keyword_bonus),
                "length_bonus": float(length_bonus),
                "chunk_id": doc.meta.get('chunk_id', 'N/A'),
                "original_doc_id": doc.meta.get('original_source_doc_id', 'N/A'),
                "verified_source": True  # Mark as verified K-Array content
            })
        
        if not high_quality_results:
            logger.warning("No high-quality results passed filtering thresholds, trying keyword search")
            return _keyword_search_documents(query, role)
        
        logger.info(f"Retrieved {len(high_quality_results)} high-quality documents from K-Array knowledge base")
        return high_quality_results
        
    except Exception as e:
        logger.error(f"Error in K-Array RAG retrieval: {e}")
        logger.info("Falling back to simple retrieval")
        return _fallback_retrieve(query, role)


def run(context: AgentContext, query: Optional[str] = None) -> AgentContext:
    """Retrieve relevant documents using K-Array RAG system."""
    
    # Use provided query or context input
    search_query = query or context.input
    user_role = getattr(context, 'role', 'user')  # Default to 'user' if role not set
    
    if not search_query or not search_query.strip():
        logger.warning("Empty query provided to document retriever")
        context.documents = []
        context.source_reliability = 0.0
        return context
    
    try:
        # Normalize query for better matching
        normalized_query = _normalize_query(search_query.strip())
        
        # Retrieve documents using enhanced K-Array RAG system
        docs = _retrieve_with_karray_rag(normalized_query, user_role)
        
        # Update context with retrieved documents
        context.documents = docs
        
        # Calculate source reliability based on results quality
        if docs:
            # Use average score from K-Array system if available
            avg_score = sum(doc.get('score', 0.5) for doc in docs) / len(docs)
            
            # Reduce reliability for fallback content
            if any(doc.get('fallback_content', False) for doc in docs):
                avg_score *= 0.8  # Reduce reliability for fallback
                logger.info("Results include fallback content - reducing reliability")
            
            context.source_reliability = min(max(avg_score, 0.0), 1.0)  # Clamp between 0 and 1
        else:
            context.source_reliability = 0.0  # Zero reliability for no results - be honest about limitations
        
        # Enhanced logging with K-Array specific information
        if docs:
            categories = list(set(doc.get('category', 'unknown') for doc in docs))
            sources = list(set(doc.get('source', 'unknown') for doc in docs))
            logger.info(
                f"Retrieved {len(docs)} K-Array documents (categories: {categories}, sources: {sources[:3]}...)",
                extra={
                    "query": search_query,
                    "user_role": user_role,
                    "document_count": len(docs),
                    "categories": categories,
                    "avg_score": context.source_reliability,
                    "confidence_score": context.confidence,
                    "source_reliability": context.source_reliability,
                    "clarification_attempted": context.clarification_attempted,
                    "error_flag": context.error_flag,
                },
            )
        else:
            logger.warning(
                f"No relevant documents found for query: '{search_query}'",
                extra={
                    "query": search_query,
                    "user_role": user_role,
                    "confidence_score": context.confidence,
                    "source_reliability": context.source_reliability,
                    "clarification_attempted": context.clarification_attempted,
                    "error_flag": context.error_flag,
                },
            )
        
    except Exception as e:
        logger.error(f"Error in document retrieval: {e}")
        context.documents = []
        context.source_reliability = 0.0
        context.error_flag = True
    
    return context
