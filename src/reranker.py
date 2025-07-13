#!/usr/bin/env python3
"""
Cross-Encoder Reranker for K-Array Chat System
Quality-focused reranking to improve retrieval precision
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from dataclasses import dataclass
from src.dynamic_config import dynamic_config

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    CrossEncoder = None


@dataclass
class RerankResult:
    """Result from reranking operation"""
    document: Dict[str, Any]
    original_score: float
    rerank_score: float
    final_score: float
    rank_change: int  # positive means moved up


class QualityReranker:
    """Cross-encoder reranker for improving retrieval quality"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"):
        self.model_name = model_name
        self.model = None
        self.setup_logging()
        self.initialize_model()
        
        # Get quality weights from dynamic configuration
        config = dynamic_config.retrieval_config
        self.semantic_weight = config.semantic_weight
        self.rerank_weight = config.rerank_weight
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def initialize_model(self):
        """Initialize cross-encoder model"""
        try:
            if not CROSS_ENCODER_AVAILABLE:
                self.logger.warning("CrossEncoder not available. Install sentence-transformers for reranking.")
                return
            
            self.logger.info(f"Loading cross-encoder model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            self.logger.info("Cross-encoder model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading cross-encoder model: {str(e)}")
            self.model = None
    
    def mock_rerank_scores(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        """Mock reranking scores when cross-encoder is not available"""
        # Simple heuristic-based scoring for fallback
        scores = []
        query_lower = query.lower()
        
        for doc in documents:
            content = doc.get('content', '').lower()
            
            # Basic scoring based on keyword matches and content quality
            score = 0.5  # base score
            
            # Keyword matching bonus
            query_words = query_lower.split()
            for word in query_words:
                if word in content:
                    score += 0.1
            
            # Content type bonus
            content_type = doc.get('metadata', {}).get('content_type', '')
            if 'technical_specs' in content_type:
                score += 0.2
            elif 'searchable_text' in content_type:
                score += 0.15
            elif 'answer' in content_type:
                score += 0.1
            
            # Product-specific bonus
            model = doc.get('metadata', {}).get('model', '').lower()
            if any(word in model for word in query_words):
                score += 0.2
            
            scores.append(min(score, 1.0))  # cap at 1.0
        
        return scores
    
    def rerank(self, 
               query: str, 
               documents: List[Dict[str, Any]], 
               top_k: Optional[int] = None) -> List[RerankResult]:
        """
        Rerank documents using cross-encoder
        
        Args:
            query: Search query
            documents: List of retrieved documents with scores
            top_k: Number of top results to return (default: all)
            
        Returns:
            List of RerankResult objects sorted by final score
        """
        
        if not documents:
            return []
        
        try:
            # Extract content and original scores
            contents = [doc.get('content', '') for doc in documents]
            original_scores = [doc.get('score', 0.0) for doc in documents]
            
            # Get reranking scores
            if self.model is not None:
                # Use actual cross-encoder
                query_content_pairs = [(query, content) for content in contents]
                rerank_scores = self.model.predict(query_content_pairs)
                
                # Convert to list if numpy array
                if hasattr(rerank_scores, 'tolist'):
                    rerank_scores = rerank_scores.tolist()
                
            else:
                # Use mock scoring
                rerank_scores = self.mock_rerank_scores(query, documents)
            
            # Combine scores
            results = []
            for i, (doc, orig_score, rerank_score) in enumerate(zip(documents, original_scores, rerank_scores)):
                # Weighted combination of original and rerank scores
                final_score = (
                    self.semantic_weight * orig_score + 
                    self.rerank_weight * rerank_score
                )
                
                results.append(RerankResult(
                    document=doc,
                    original_score=orig_score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                    rank_change=0  # Will be calculated after sorting
                ))
            
            # Sort by final score
            results.sort(key=lambda x: x.final_score, reverse=True)
            
            # Calculate rank changes
            for new_rank, result in enumerate(results):
                # Find original rank
                original_rank = next(
                    i for i, doc in enumerate(documents) 
                    if doc.get('id') == result.document.get('id')
                )
                result.rank_change = original_rank - new_rank
            
            # Apply top_k if specified
            if top_k is not None:
                results = results[:top_k]
            
            self.logger.info(f"Reranked {len(documents)} documents, returning top {len(results)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during reranking: {str(e)}")
            # Return original order as fallback
            return [
                RerankResult(
                    document=doc,
                    original_score=doc.get('score', 0.0),
                    rerank_score=0.0,
                    final_score=doc.get('score', 0.0),
                    rank_change=0
                ) for doc in documents
            ]
    
    def get_reranked_documents(self, 
                              query: str, 
                              documents: List[Dict[str, Any]], 
                              top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get reranked documents in standard format
        
        Returns:
            List of documents with updated scores
        """
        rerank_results = self.rerank(query, documents, top_k)
        
        # Convert back to standard format
        reranked_docs = []
        for result in rerank_results:
            doc = result.document.copy()
            doc['score'] = result.final_score
            doc['rerank_metadata'] = {
                'original_score': result.original_score,
                'rerank_score': result.rerank_score,
                'rank_change': result.rank_change
            }
            reranked_docs.append(doc)
        
        return reranked_docs
    
    def analyze_query_type(self, query: str) -> str:
        """Analyze query to determine optimal reranking strategy"""
        query_lower = query.lower()
        
        # Technical specification queries
        tech_keywords = ['specs', 'specifications', 'power', 'frequency', 'dimensions', 'weight']
        if any(keyword in query_lower for keyword in tech_keywords):
            return 'technical'
        
        # Product comparison queries
        if any(word in query_lower for word in ['vs', 'versus', 'compare', 'difference']):
            return 'comparison'
        
        # Application/usage queries
        app_keywords = ['application', 'use', 'install', 'setup', 'how to']
        if any(keyword in query_lower for keyword in app_keywords):
            return 'application'
        
        return 'general'
    
    def quality_metrics(self, 
                       query: str, 
                       original_docs: List[Dict[str, Any]], 
                       reranked_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality improvement metrics"""
        
        if not original_docs or not reranked_docs:
            return {}
        
        # Calculate average score improvement
        orig_avg = sum(doc.get('score', 0) for doc in original_docs) / len(original_docs)
        rerank_avg = sum(doc.get('score', 0) for doc in reranked_docs) / len(reranked_docs)
        
        # Count rank changes
        significant_changes = sum(
            1 for doc in reranked_docs 
            if abs(doc.get('rerank_metadata', {}).get('rank_change', 0)) >= 2
        )
        
        return {
            'original_avg_score': orig_avg,
            'reranked_avg_score': rerank_avg,
            'score_improvement': rerank_avg - orig_avg,
            'significant_rank_changes': significant_changes,
            'query_type': self.analyze_query_type(query),
            'model_used': 'cross_encoder' if self.model else 'heuristic'
        }


if __name__ == "__main__":
    # Test the reranker
    try:
        reranker = QualityReranker()
        print("✅ Reranker initialized successfully")
        
        # Mock test data
        test_docs = [
            {
                'id': '1',
                'content': 'KA02I amplifier specifications power 50W',
                'score': 0.8,
                'metadata': {'content_type': 'technical_specs', 'model': 'KA02I'}
            },
            {
                'id': '2', 
                'content': 'General information about K-Array products',
                'score': 0.9,
                'metadata': {'content_type': 'general', 'model': ''}
            }
        ]
        
        results = reranker.rerank("KA02I specifications", test_docs)
        print(f"✅ Reranking test completed - {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. Score: {result.final_score:.3f} "
                  f"(orig: {result.original_score:.3f}, rerank: {result.rerank_score:.3f})")
        
    except Exception as e:
        print(f"❌ Error testing reranker: {e}")