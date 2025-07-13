#!/usr/bin/env python3
"""
Smart Retriever for K-Array Chat System
Implements intelligent retrieval with context awareness and query analysis
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

from src.enhanced_vector_store import EnhancedVectorStore
from src.reranker import QualityReranker


@dataclass
class RetrievalContext:
    """Context for retrieval including query analysis and filters"""
    original_query: str
    processed_query: str
    query_type: str  # 'technical', 'application', 'comparison', 'general'
    detected_products: List[str]
    detected_categories: List[str]
    intent: str  # 'specs', 'usage', 'comparison', 'troubleshooting'
    confidence: float


class SmartRetriever:
    """Intelligent retriever with context awareness and query optimization"""
    
    def __init__(self, vector_store: EnhancedVectorStore, enable_reranking: bool = True):
        self.vector_store = vector_store
        self.enable_reranking = enable_reranking
        self.reranker = QualityReranker() if enable_reranking else None
        self.setup_logging()
        
        # Knowledge patterns for query analysis
        self.product_patterns = {
            'kommander': r'ka[0-9]+[a-z]*|kommander|ka02i|ka04|ka02',
            'lyzard': r'k[xz][0-9]+|lyzard',
            'vyper': r'kv[0-9]+|vyper',
            'thunder': r'k[ms][t]*[0-9]+|thunder',
            'python': r'kp[0-9]+|python',
            'kobra': r'kk[0-9]+|kobra',
            'domino': r'kf[0-9]+|domino',
            'dragon': r'kx[0-9]+|dragon',
            'mugello': r'kh[0-9]+|mugello',
            'firenze': r'k[hs][0-9]+|firenze',
            'rumble': r'ku[0-9]+|rumble',
            'truffle': r'ktr[0-9]+|truffle',
            'azimut': r'kamut[0-9]+|azimut',
            'pinnacle': r'kr[0-9]+|pinnacle',
            'mastiff': r'km[0-9]+|mastiff',
            'turtle': r'krm[0-9]+|turtle',
            'anakonda': r'kan[0-9]+|anakonda',
            'kayman': r'ky[0-9]+|kayman',
            'capture': r'kmc[0-9]+|capture',
            'duetto': r'kd[0-9]+|duetto',
            'axle': r'krx[0-9]+|axle',
            'event': r'krev[0-9]+|event'
        }
        
        self.technical_keywords = [
            'power', 'watt', 'frequency', 'hz', 'spl', 'db', 'ohm', 'impedance',
            'dimension', 'weight', 'material', 'mounting', 'input', 'output',
            'voltage', 'current', 'amplifier', 'speaker', 'driver', 'transducer'
        ]
        
        self.application_keywords = [
            'hotel', 'restaurant', 'retail', 'museum', 'theater', 'church',
            'fitness', 'spa', 'marine', 'hospitality', 'concert', 'live'
        ]
        
        self.intent_patterns = {
            'specs': r'specification|spec|power|frequency|dimension|weight|technical',
            'usage': r'application|use|suitable|recommend|where|install',
            'comparison': r'compare|difference|vs|versus|better|best',
            'troubleshooting': r'problem|issue|not working|error|fix'
        }
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_query(self, query: str) -> RetrievalContext:
        """Analyze query to understand intent and extract context"""
        query_lower = query.lower()
        
        # Detect products
        detected_products = []
        for product_line, pattern in self.product_patterns.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                detected_products.append(product_line)
        
        # Detect query type
        technical_score = sum(1 for kw in self.technical_keywords if kw in query_lower)
        application_score = sum(1 for kw in self.application_keywords if kw in query_lower)
        
        if technical_score > application_score:
            query_type = 'technical'
        elif application_score > 0:
            query_type = 'application'
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
            query_type = 'comparison'
        else:
            query_type = 'general'
        
        # Detect intent
        intent = 'general'
        max_intent_score = 0
        for intent_name, pattern in self.intent_patterns.items():
            if re.search(pattern, query_lower):
                intent = intent_name
                break
        
        # Calculate confidence
        confidence = min(1.0, (technical_score + application_score + len(detected_products)) / 5)
        
        # Process query for better search
        processed_query = self.preprocess_query(query)
        
        return RetrievalContext(
            original_query=query,
            processed_query=processed_query,
            query_type=query_type,
            detected_products=detected_products,
            detected_categories=[],  # Will be enhanced later
            intent=intent,
            confidence=confidence
        )
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess query for better retrieval"""
        # Expand abbreviations
        expansions = {
            'amp': 'amplifier',
            'spec': 'specification',
            'freq': 'frequency',
            'dim': 'dimension'
        }
        
        processed = query.lower()
        for abbr, full in expansions.items():
            processed = re.sub(r'\b' + abbr + r'\b', full, processed)
        
        return processed
    
    def retrieve_contextual(self, 
                           context: RetrievalContext,
                           max_results: int = 10) -> List[Dict[str, Any]]:
        """Retrieve documents based on context analysis"""
        
        all_results = []
        
        # Strategy 1: QA pairs for specific questions
        if context.intent in ['specs', 'usage']:
            qa_results = self.vector_store.search(
                context.processed_query, 
                top_k=3,
                filters={'content_type': ['question', 'answer']}
            )
            all_results.extend(self._tag_results(qa_results, 'qa_direct'))
        
        # Strategy 2: Technical specs for technical queries
        if context.query_type == 'technical':
            spec_results = self.vector_store.search(
                context.processed_query,
                top_k=2,
                filters={'content_type': 'technical_specs'}
            )
            all_results.extend(self._tag_results(spec_results, 'technical_specs'))
        
        # Strategy 3: Product-specific search if products detected
        if context.detected_products:
            for product in context.detected_products[:2]:  # Limit to 2 products
                product_results = self.vector_store.search(
                    query=context.processed_query,
                    top_k=3,
                    filters={'product_line': product.title()}
                )
                all_results.extend(self._tag_results(product_results, f'product_{product}'))
        
        # Strategy 4: Semantic chunks for general understanding
        semantic_results = self.vector_store.search(
            query=context.processed_query,
            top_k=5,
            filters={'content_type': 'semantic_chunk'}
        )
        all_results.extend(self._tag_results(semantic_results, 'semantic'))
        
        # Strategy 5: General searchable text
        general_results = self.vector_store.search(
            query=context.processed_query,
            top_k=3,
            filters={'content_type': 'searchable_text'}
        )
        all_results.extend(self._tag_results(general_results, 'general'))
        
        # Remove duplicates and rank
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, context)
        
        # Apply reranking if enabled
        if self.enable_reranking and self.reranker and ranked_results:
            try:
                # Get more results for reranking (expand then narrow)
                expanded_results = ranked_results[:max_results * 2] if len(ranked_results) > max_results else ranked_results
                reranked_results = self.reranker.get_reranked_documents(
                    context.original_query, 
                    expanded_results, 
                    top_k=max_results
                )
                
                self.logger.info(f"Applied reranking to {len(expanded_results)} results, returning top {len(reranked_results)}")
                return reranked_results
                
            except Exception as e:
                self.logger.warning(f"Reranking failed, using original ranking: {str(e)}")
        
        self.logger.info(f"Retrieved {len(ranked_results)} unique results for query: {context.original_query}")
        
        return ranked_results[:max_results]
    
    def _tag_results(self, results: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
        """Tag results with retrieval strategy"""
        for result in results:
            result['retrieval_strategy'] = strategy
        return results
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on content similarity"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            # Create a simplified content hash
            content_hash = hash(result['content'][:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, 
                     results: List[Dict[str, Any]], 
                     context: RetrievalContext) -> List[Dict[str, Any]]:
        """Rank results based on relevance and retrieval strategy"""
        
        # Strategy weights
        strategy_weights = {
            'qa_direct': 1.0,
            'technical_specs': 0.9,
            'semantic': 0.8,
            'general': 0.7
        }
        
        # Add strategy-based weights for product searches
        for product in context.detected_products:
            strategy_weights[f'product_{product}'] = 0.95
        
        for result in results:
            base_score = result.get('similarity', 0.5)
            strategy_weight = strategy_weights.get(result.get('retrieval_strategy', 'general'), 0.7)
            
            # Boost score for exact product matches
            content_lower = result['content'].lower()
            product_boost = 0
            for product in context.detected_products:
                if product.lower() in content_lower:
                    product_boost += 0.1
            
            # Boost score for intent matching
            intent_boost = 0
            if context.intent == 'specs' and 'specification' in content_lower:
                intent_boost = 0.1
            elif context.intent == 'usage' and any(app in content_lower for app in self.application_keywords):
                intent_boost = 0.1
            
            # Final score calculation
            result['final_score'] = (base_score * strategy_weight) + product_boost + intent_boost
        
        # Sort by final score
        return sorted(results, key=lambda x: x.get('final_score', 0), reverse=True)
    
    def get_conversation_context(self, 
                               conversation_history: List[Dict[str, str]],
                               current_query: str) -> RetrievalContext:
        """Analyze conversation history to improve current query context"""
        
        # Extract mentioned products from conversation history
        mentioned_products = set()
        conversation_text = ""
        
        for message in conversation_history[-3:]:  # Look at last 3 messages
            if message.get('role') in ['user', 'assistant']:
                text = message.get('content', '').lower()
                conversation_text += text + " "
                
                # Extract products from history
                for product_line, pattern in self.product_patterns.items():
                    if re.search(pattern, text, re.IGNORECASE):
                        mentioned_products.add(product_line)
        
        # Analyze current query with conversation context
        base_context = self.analyze_query(current_query)
        
        # Enhance with conversation context
        if mentioned_products and not base_context.detected_products:
            base_context.detected_products = list(mentioned_products)
            base_context.confidence = min(1.0, base_context.confidence + 0.2)
        
        # Create enhanced query if context provides additional info
        if conversation_text and len(conversation_text.strip()) > 10:
            enhanced_query = f"{current_query} {conversation_text[:200]}"
            base_context.processed_query = self.preprocess_query(enhanced_query)
        
        return base_context
    
    def search(self, 
               query: str, 
               conversation_history: Optional[List[Dict[str, str]]] = None,
               max_results: int = 5) -> Tuple[List[Dict[str, Any]], RetrievalContext]:
        """Main search interface with conversation awareness"""
        
        # Analyze query with conversation context
        if conversation_history:
            context = self.get_conversation_context(conversation_history, query)
        else:
            context = self.analyze_query(query)
        
        # Retrieve contextual results
        results = self.retrieve_contextual(context, max_results)
        
        return results, context


if __name__ == "__main__":
    # Test the smart retriever
    from src.enhanced_vector_store import EnhancedVectorStore
    
    vector_store = EnhancedVectorStore()
    retriever = SmartRetriever(vector_store)
    
    # Test query analysis
    context = retriever.analyze_query("What are the power specifications of the Kommander KA104?")
    print(f"Query type: {context.query_type}")
    print(f"Intent: {context.intent}")
    print(f"Detected products: {context.detected_products}")
    print(f"Confidence: {context.confidence}")
    
    # Test search
    results, context = retriever.search("amplifier power specifications")
    print(f"\nFound {len(results)} results")
    for result in results[:2]:
        print(f"Content: {result['content'][:100]}...")
        print(f"Strategy: {result.get('retrieval_strategy')}")
        print(f"Score: {result.get('final_score', 0):.3f}")
        print("---")