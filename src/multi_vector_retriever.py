#!/usr/bin/env python3
"""
Multi-Vector Retrieval System for K-Array Chat System
Combines multiple retrieval strategies for maximum quality
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import re
from collections import defaultdict

from src.enhanced_vector_store import EnhancedVectorStore
from src.reranker import QualityReranker
from src.query_intelligence import QueryIntelligenceEngine, QueryIntelligence
from src.dynamic_config import dynamic_config


@dataclass
class RetrievalStrategy:
    """Configuration for a retrieval strategy"""
    name: str
    weight: float
    filters: Optional[Dict[str, Any]] = None
    query_transform: Optional[str] = None
    enabled: bool = True


@dataclass
class MultiVectorResult:
    """Result from multi-vector retrieval"""
    document: Dict[str, Any]
    combined_score: float
    strategy_scores: Dict[str, float]
    strategy_ranks: Dict[str, int]
    confidence: float


class MultiVectorRetriever:
    """Advanced multi-vector retrieval system for maximum quality"""
    
    def __init__(self, 
                 vector_store: EnhancedVectorStore,
                 enable_reranking: bool = True,
                 enable_fusion: bool = True,
                 enable_query_intelligence: bool = True):
        
        self.vector_store = vector_store
        self.enable_reranking = enable_reranking
        self.enable_fusion = enable_fusion
        self.enable_query_intelligence = enable_query_intelligence
        
        self.reranker = QualityReranker() if enable_reranking else None
        self.query_intelligence = QueryIntelligenceEngine() if enable_query_intelligence else None
        
        self.setup_logging()
        self.initialize_strategies()
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def initialize_strategies(self):
        """Initialize different retrieval strategies with dynamic configuration"""
        
        # Get weights from configuration
        config = dynamic_config.retrieval_config
        
        # Define retrieval strategies with configurable weights
        self.strategies = {
            # High-precision strategies (higher weight)
            'exact_product_match': RetrievalStrategy(
                name='exact_product_match',
                weight=config.exact_product_weight,
                filters={'content_type': ['technical_specs', 'searchable_text']},
                query_transform='product_focused' if config.enable_product_focused_transform else None
            ),
            
            'qa_pairs': RetrievalStrategy(
                name='qa_pairs', 
                weight=config.qa_pairs_weight,
                filters={'content_type': ['question', 'answer']},
                query_transform='question_format'
            ),
            
            'technical_specs': RetrievalStrategy(
                name='technical_specs',
                weight=config.technical_specs_weight,
                filters={'content_type': 'technical_specs'},
                query_transform='technical_focused' if config.enable_technical_transform else None
            ),
            
            # Medium-precision strategies 
            'semantic_chunks': RetrievalStrategy(
                name='semantic_chunks',
                weight=config.semantic_chunks_weight,
                filters={'content_type': 'semantic_chunk'},
                query_transform='semantic_expansion' if config.enable_semantic_expansion else None
            ),
            
            'searchable_content': RetrievalStrategy(
                name='searchable_content',
                weight=config.searchable_content_weight,
                filters={'content_type': 'searchable_text'},
                query_transform='content_optimization'
            ),
            
            # Broad-coverage strategies (lower weight but important for recall)
            'hybrid_search': RetrievalStrategy(
                name='hybrid_search',
                weight=config.hybrid_search_weight,
                filters=None,  # No filters for broad coverage
                query_transform='query_expansion'
            )
        }
        
        # Quality-focused query transformations
        self.query_transformations = {
            'product_focused': self._transform_product_focused,
            'question_format': self._transform_question_format,
            'technical_focused': self._transform_technical_focused,
            'semantic_expansion': self._transform_semantic_expansion,
            'content_optimization': self._transform_content_optimization,
            'query_expansion': self._transform_query_expansion
        }
    
    def _transform_product_focused(self, query: str) -> str:
        """Transform query to focus on product identification"""
        # Extract product codes and enhance them
        products = re.findall(r'k[a-z]*[0-9]+[a-z]*', query.lower())
        if products:
            main_product = products[0].upper()
            return f"{main_product} {query}"
        return query
    
    def _transform_question_format(self, query: str) -> str:
        """Transform query to question format for QA matching"""
        if not query.strip().endswith('?'):
            # Convert to question format
            if any(word in query.lower() for word in ['what', 'how', 'where', 'when', 'why', 'which']):
                return query + '?'
            else:
                return f"What {query}?"
        return query
    
    def _transform_technical_focused(self, query: str) -> str:
        """Transform query to emphasize technical aspects"""
        tech_keywords = ['specifications', 'specs', 'technical', 'parameters']
        if not any(kw in query.lower() for kw in tech_keywords):
            return f"{query} specifications technical details"
        return query
    
    def _transform_semantic_expansion(self, query: str) -> str:
        """Expand query with semantic synonyms from dynamic configuration"""
        
        # Get expansions from dynamic configuration
        expansions = dynamic_config.get_query_expansions()
        
        expanded = query
        for term, expansion in expansions.items():
            if term in query.lower():
                expanded = f"{expanded} {expansion}"
        
        return expanded
    
    def _transform_content_optimization(self, query: str) -> str:
        """Optimize query for general content search"""
        # Remove question words that might reduce semantic matching
        optimized = re.sub(r'\b(what|how|where|when|why|which|is|are|can|does)\b', '', query, flags=re.IGNORECASE)
        return optimized.strip()
    
    def _transform_query_expansion(self, query: str) -> str:
        """Expand query with related terms"""
        # Add common K-Array terminology
        if re.search(r'k[a-z]*[0-9]+', query.lower()):
            return f"{query} K-Array audio speaker amplifier"
        return query
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine optimal strategy weights"""
        query_lower = query.lower()
        
        # Product-specific query detection
        products = re.findall(r'k[a-z]*[0-9]+[a-z]*', query_lower)
        has_product = len(products) > 0
        
        # Technical query detection
        tech_indicators = ['spec', 'power', 'frequency', 'dimension', 'weight', 'technical']
        is_technical = any(indicator in query_lower for indicator in tech_indicators)
        
        # Question format detection
        is_question = any(query_lower.startswith(q) for q in ['what', 'how', 'where', 'which', 'when', 'why'])
        
        # Comparison query detection
        is_comparison = any(comp in query_lower for comp in ['vs', 'versus', 'compare', 'difference', 'better'])
        
        return {
            'has_product': has_product,
            'products': products,
            'is_technical': is_technical,
            'is_question': is_question,
            'is_comparison': is_comparison,
            'query_complexity': len(query.split())
        }
    
    def adjust_strategy_weights(self, query_intent: Dict[str, Any]) -> Dict[str, RetrievalStrategy]:
        """Adjust strategy weights based on query intent"""
        adjusted_strategies = {}
        
        for name, strategy in self.strategies.items():
            adjusted_strategy = RetrievalStrategy(
                name=strategy.name,
                weight=strategy.weight,
                filters=strategy.filters,
                query_transform=strategy.query_transform,
                enabled=strategy.enabled
            )
            
            # Boost weights based on query intent
            if query_intent['has_product'] and name == 'exact_product_match':
                adjusted_strategy.weight *= 1.5
            
            if query_intent['is_technical'] and name == 'technical_specs':
                adjusted_strategy.weight *= 1.3
                
            if query_intent['is_question'] and name == 'qa_pairs':
                adjusted_strategy.weight *= 1.4
            
            # Normalize to ensure total weight ≤ 1.0
            adjusted_strategies[name] = adjusted_strategy
        
        # Normalize weights
        total_weight = sum(s.weight for s in adjusted_strategies.values() if s.enabled)
        if total_weight > 1.0:
            for strategy in adjusted_strategies.values():
                strategy.weight /= total_weight
        
        return adjusted_strategies
    
    def adjust_strategy_weights_intelligent(self, query_intelligence: QueryIntelligence) -> Dict[str, RetrievalStrategy]:
        """Adjust strategy weights based on LLM query intelligence"""
        adjusted_strategies = {}
        
        for name, strategy in self.strategies.items():
            adjusted_strategy = RetrievalStrategy(
                name=strategy.name,
                weight=strategy.weight,
                filters=strategy.filters,
                query_transform=strategy.query_transform,
                enabled=strategy.enabled
            )
            
            # Intent-based weight adjustments
            if query_intelligence.intent.value == 'technical_specs_only':
                if name in ['technical_specs', 'exact_product_match']:
                    adjusted_strategy.weight *= 2.0
                elif name in ['qa_pairs']:
                    adjusted_strategy.weight *= 1.5
                elif name in ['searchable_content']:
                    adjusted_strategy.weight *= 0.3  # Reduce general content
                    
            elif query_intelligence.intent.value == 'applications_only':
                if name in ['qa_pairs', 'semantic_chunks']:
                    adjusted_strategy.weight *= 1.8
                elif name in ['technical_specs']:
                    adjusted_strategy.weight *= 0.2  # Reduce technical focus
                    
            elif query_intelligence.intent.value == 'product_comparison':
                if name in ['exact_product_match', 'technical_specs']:
                    adjusted_strategy.weight *= 1.6
                elif name in ['hybrid_search']:
                    adjusted_strategy.weight *= 1.3
                    
            # Product-specific boosts
            if query_intelligence.products_mentioned:
                if name == 'exact_product_match':
                    adjusted_strategy.weight *= 1.5
            
            # Complexity adjustments
            if query_intelligence.complexity.value == 'simple':
                if name in ['exact_product_match', 'qa_pairs']:
                    adjusted_strategy.weight *= 1.3
            elif query_intelligence.complexity.value == 'complex':
                if name == 'hybrid_search':
                    adjusted_strategy.weight *= 1.4
            
            adjusted_strategies[name] = adjusted_strategy
        
        # Normalize weights
        total_weight = sum(s.weight for s in adjusted_strategies.values() if s.enabled)
        if total_weight > 1.0:
            for strategy in adjusted_strategies.values():
                strategy.weight /= total_weight
        
        return adjusted_strategies
    
    def retrieve_with_strategy(self, 
                              query: str, 
                              strategy: RetrievalStrategy,
                              top_k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve documents using a specific strategy"""
        
        try:
            # Apply query transformation
            if strategy.query_transform and strategy.query_transform in self.query_transformations:
                transformed_query = self.query_transformations[strategy.query_transform](query)
            else:
                transformed_query = query
            
            # Perform search with strategy-specific filters
            results = self.vector_store.search(
                query=transformed_query,
                top_k=top_k,
                filters=strategy.filters
            )
            
            # Tag results with strategy info
            for result in results:
                result['retrieval_strategy'] = strategy.name
                result['strategy_weight'] = strategy.weight
                result['transformed_query'] = transformed_query
            
            self.logger.debug(f"Strategy '{strategy.name}' retrieved {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.warning(f"Strategy '{strategy.name}' failed: {str(e)}")
            return []
    
    def reciprocal_rank_fusion(self, 
                              strategy_results: Dict[str, List[Dict[str, Any]]],
                              k: int = 60) -> List[MultiVectorResult]:
        """Combine results from multiple strategies using Reciprocal Rank Fusion"""
        
        # Collect all unique documents
        doc_scores = defaultdict(lambda: {'scores': {}, 'ranks': {}, 'document': None})
        
        for strategy_name, results in strategy_results.items():
            strategy_weight = self.strategies[strategy_name].weight
            
            for rank, result in enumerate(results):
                doc_id = result.get('id', f"unknown_{rank}")
                
                # RRF score: weight * (1 / (k + rank))
                rrf_score = strategy_weight * (1.0 / (k + rank + 1))
                
                doc_scores[doc_id]['scores'][strategy_name] = rrf_score
                doc_scores[doc_id]['ranks'][strategy_name] = rank + 1
                doc_scores[doc_id]['document'] = result
        
        # Calculate combined scores and confidence
        multi_results = []
        for doc_id, data in doc_scores.items():
            combined_score = sum(data['scores'].values())
            
            # Confidence based on strategy agreement
            num_strategies = len(data['scores'])
            max_strategies = len([s for s in self.strategies.values() if s.enabled])
            confidence = num_strategies / max_strategies
            
            multi_results.append(MultiVectorResult(
                document=data['document'],
                combined_score=combined_score,
                strategy_scores=data['scores'],
                strategy_ranks=data['ranks'],
                confidence=confidence
            ))
        
        # Sort by combined score
        multi_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        return multi_results
    
    def retrieve(self, 
                query: str, 
                max_results: int = 5,
                strategy_results_per_query: int = 10,
                conversation_history: Optional[List[Dict[str, str]]] = None) -> Tuple[List[Dict[str, Any]], Optional[QueryIntelligence]]:
        """
        Main multi-vector retrieval method with query intelligence
        
        Args:
            query: Search query
            max_results: Maximum number of final results
            strategy_results_per_query: Results per strategy before fusion
            conversation_history: Previous conversation context
            
        Returns:
            Tuple of (documents with enhanced scoring, query intelligence result)
        """
        
        self.logger.info(f"Multi-vector retrieval for query: '{query}'")
        
        # Step 1: Query Intelligence Analysis
        query_intelligence = None
        optimized_query = query
        
        if self.enable_query_intelligence and self.query_intelligence:
            try:
                query_intelligence = self.query_intelligence.analyze_query(query, conversation_history)
                optimized_query = query_intelligence.optimized_query
                self.logger.info(f"Query optimized: '{query}' → '{optimized_query}'")
                self.logger.info(f"Intent: {query_intelligence.intent.value}, "
                               f"Confidence: {query_intelligence.confidence:.2f}")
                
                # Check if clarification is needed
                if self.query_intelligence.should_ask_clarification(query_intelligence):
                    clarification = self.query_intelligence.generate_clarification_question(query_intelligence)
                    self.logger.info(f"Clarification suggested: {clarification}")
                    # Could return early here with clarification request
                    
            except Exception as e:
                self.logger.warning(f"Query intelligence failed, using original query: {str(e)}")
                optimized_query = query
        
        # Step 2: Analyze query intent (fallback/additional analysis)
        query_intent = self.analyze_query_intent(optimized_query)
        self.logger.debug(f"Query intent analysis: {query_intent}")
        
        # Step 3: Adjust strategy weights based on intent and intelligence
        if query_intelligence:
            adjusted_strategies = self.adjust_strategy_weights_intelligent(query_intelligence)
        else:
            adjusted_strategies = self.adjust_strategy_weights(query_intent)
        
        # Step 4: Execute all enabled strategies with optimized query
        strategy_results = {}
        for name, strategy in adjusted_strategies.items():
            if strategy.enabled:
                results = self.retrieve_with_strategy(
                    optimized_query,  # Use optimized query from intelligence
                    strategy, 
                    top_k=strategy_results_per_query
                )
                if results:
                    strategy_results[name] = results
        
        self.logger.info(f"Executed {len(strategy_results)} retrieval strategies")
        
        # Combine results using Reciprocal Rank Fusion
        if not strategy_results:
            self.logger.warning("No strategy results available")
            return []
        
        fused_results = self.reciprocal_rank_fusion(strategy_results)
        
        # Apply reranking if enabled
        if self.enable_reranking and self.reranker and fused_results:
            try:
                # Extract documents for reranking
                documents_for_reranking = [result.document for result in fused_results[:max_results * 2]]
                
                reranked_docs = self.reranker.get_reranked_documents(
                    query, 
                    documents_for_reranking, 
                    top_k=max_results
                )
                
                self.logger.info(f"Applied reranking to {len(documents_for_reranking)} fused results")
                
                # Enhance with multi-vector metadata
                final_results = []
                for doc in reranked_docs:
                    # Find corresponding multi-vector result
                    multi_result = next(
                        (mr for mr in fused_results if mr.document.get('id') == doc.get('id')),
                        None
                    )
                    
                    if multi_result:
                        doc['multi_vector_metadata'] = {
                            'combined_score': multi_result.combined_score,
                            'strategy_scores': multi_result.strategy_scores,
                            'strategy_ranks': multi_result.strategy_ranks,
                            'confidence': multi_result.confidence,
                            'num_strategies': len(multi_result.strategy_scores)
                        }
                    
                    final_results.append(doc)
                
                return final_results, query_intelligence
                
            except Exception as e:
                self.logger.warning(f"Reranking failed, using fusion results: {str(e)}")
        
        # Return fusion results without reranking
        final_results = []
        for result in fused_results[:max_results]:
            doc = result.document
            doc['multi_vector_metadata'] = {
                'combined_score': result.combined_score,
                'strategy_scores': result.strategy_scores,
                'strategy_ranks': result.strategy_ranks,
                'confidence': result.confidence,
                'num_strategies': len(result.strategy_scores)
            }
            final_results.append(doc)
        
        self.logger.info(f"Returning {len(final_results)} multi-vector results")
        return final_results, query_intelligence
    
    def get_quality_metrics(self, 
                           query: str, 
                           results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for multi-vector retrieval"""
        
        if not results:
            return {'error': 'No results to analyze'}
        
        # Strategy coverage
        strategies_used = set()
        confidence_scores = []
        
        for result in results:
            metadata = result.get('multi_vector_metadata', {})
            strategies_used.update(metadata.get('strategy_scores', {}).keys())
            confidence_scores.append(metadata.get('confidence', 0.0))
        
        # Quality indicators
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        strategy_coverage = len(strategies_used) / len(self.strategies)
        
        # Reranking impact
        reranking_applied = any('rerank_metadata' in result for result in results)
        
        return {
            'average_confidence': avg_confidence,
            'strategy_coverage': strategy_coverage,
            'strategies_used': list(strategies_used),
            'total_strategies_available': len(self.strategies),
            'reranking_applied': reranking_applied,
            'query_intent': self.analyze_query_intent(query),
            'result_count': len(results)
        }


if __name__ == "__main__":
    # Test the multi-vector retriever
    try:
        from src.enhanced_vector_store import EnhancedVectorStore
        
        # Mock vector store for testing
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return [
                    {
                        'id': f'mock_{i}',
                        'content': f'Mock content {i} for: {query}',
                        'score': 0.9 - (i * 0.1),
                        'metadata': {'content_type': 'searchable_text'}
                    } for i in range(min(top_k, 3))
                ]
        
        mock_store = MockVectorStore()
        retriever = MultiVectorRetriever(mock_store)
        
        print("✅ Multi-vector retriever initialized")
        
        # Test retrieval
        results = retriever.retrieve("KA02I technical specifications", max_results=3)
        print(f"✅ Retrieved {len(results)} results")
        
        # Test quality metrics
        metrics = retriever.get_quality_metrics("KA02I technical specifications", results)
        print(f"✅ Quality metrics: confidence={metrics['average_confidence']:.3f}")
        
    except Exception as e:
        print(f"❌ Error testing multi-vector retriever: {e}")