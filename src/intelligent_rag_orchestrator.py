#!/usr/bin/env python3
"""
Intelligent RAG Orchestrator for K-Array Chat System
LLM-driven multi-stage retrieval with adaptive strategies and iterative refinement
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import difflib

from src.llm_manager import LLMManager
from src.local_vector_store import LocalVectorStore
from src.dynamic_config import dynamic_config


class RAGStage(Enum):
    """RAG processing stages"""
    QUERY_ANALYSIS = "query_analysis"
    INITIAL_SEARCH = "initial_search"
    RESULT_EVALUATION = "result_evaluation"
    ITERATIVE_SEARCH = "iterative_search"
    SYNTHESIS = "synthesis"
    FINAL_ANSWER = "final_answer"


@dataclass
class SearchStrategy:
    """Search strategy determined by LLM"""
    strategy_type: str  # exact, fuzzy, semantic, hybrid, exploratory
    search_terms: List[str]
    filters: Dict[str, Any]
    top_k: int
    confidence_threshold: float
    explanation: str


@dataclass
class RAGResult:
    """Result from a RAG operation"""
    stage: RAGStage
    strategy_used: SearchStrategy
    documents: List[Dict[str, Any]]
    confidence: float
    needs_refinement: bool
    refinement_suggestions: List[str]
    synthesis: str


class IntelligentRAGOrchestrator:
    """LLM-orchestrated multi-stage RAG system"""
    
    def __init__(self, vector_store: LocalVectorStore, llm_manager: LLMManager):
        self.vector_store = vector_store
        self.llm_manager = llm_manager
        self.setup_logging()
        
        # Knowledge base for product matching
        self.load_product_knowledge()
        
        # Conversation context
        self.conversation_context = []
        
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def load_product_knowledge(self):
        """Load comprehensive product knowledge for fuzzy matching"""
        # This would be populated from the actual product database
        self.product_knowledge = {
            'products': {
                # Kommander Series
                'ka104': {'aliases': ['ka104', 'kommander ka104', 'kommander-ka104'], 'series': 'kommander'},
                'ka104live': {'aliases': ['ka104live', 'ka104-live', 'kommander ka104live'], 'series': 'kommander'},
                'ka208': {'aliases': ['ka208', 'kommander ka208', 'kommander-ka208'], 'series': 'kommander'},
                'ka02i': {'aliases': ['ka02i', 'ka02-i', 'kommander ka02i'], 'series': 'kommander'},
                
                # Software/Framework
                'k-framework': {'aliases': ['k framework', 'k-framework', 'k framework 3', 'kframework'], 'series': 'software'},
                
                # Lyzard Series  
                'kz1i': {'aliases': ['kz1i', 'kz1-i', 'lyzard kz1i', 'lyzard-kz1i'], 'series': 'lyzard'},
                'kz14i': {'aliases': ['kz14i', 'kz14-i', 'lyzard kz14i'], 'series': 'lyzard'},
                
                # Vyper Series
                'kv25i': {'aliases': ['kv25i', 'kv25-i', 'vyper kv25i'], 'series': 'vyper'},
            },
            'series': {
                'kommander': ['amplifier', 'controller', 'processing'],
                'lyzard': ['line array', 'speaker', 'audio'],
                'vyper': ['line array', 'speaker', 'high power'],
                'software': ['framework', 'control', 'dsp', 'management']
            }
        }
    
    def fuzzy_match_products(self, query: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """Fuzzy match products using difflib and aliases"""
        matches = []
        query_lower = query.lower()
        
        for product_id, product_data in self.product_knowledge['products'].items():
            # Check exact aliases first
            for alias in product_data['aliases']:
                if alias.lower() in query_lower:
                    matches.append((product_id, 1.0))
                    break
            else:
                # Fuzzy matching against product ID and main aliases
                for alias in product_data['aliases'][:2]:  # Check main aliases
                    similarity = difflib.SequenceMatcher(None, query_lower, alias.lower()).ratio()
                    if similarity >= threshold:
                        matches.append((product_id, similarity))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]  # Top 5 matches
    
    def analyze_query_with_llm(self, user_query: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Let LLM analyze the query and determine search strategy"""
        
        # Include fuzzy matches in the analysis
        fuzzy_matches = self.fuzzy_match_products(user_query)
        
        analysis_prompt = f"""
        Analyze this user query for a K-Array audio equipment database search:
        
        USER QUERY: "{user_query}"
        
        FUZZY PRODUCT MATCHES FOUND:
        {json.dumps(fuzzy_matches, indent=2) if fuzzy_matches else "No close matches found"}
        
        AVAILABLE PRODUCT KNOWLEDGE:
        {json.dumps(self.product_knowledge, indent=2)}
        
        CONVERSATION CONTEXT:
        {json.dumps(context[-3:] if context else [], indent=2)}
        
        Provide a JSON response with:
        {{
            "intent": "technical_specs|comparison|applications|troubleshooting|general_info|product_search",
            "detected_products": ["product1", "product2"],  // Based on fuzzy matches and analysis
            "search_strategies": [
                {{
                    "strategy_type": "exact|fuzzy|semantic|hybrid|exploratory", 
                    "search_terms": ["term1", "term2"],
                    "filters": {{"category": "value", "series": "value"}},
                    "top_k": 10,
                    "confidence_threshold": 0.7,
                    "explanation": "Why this strategy"
                }}
            ],
            "query_complexity": "simple|moderate|complex",
            "needs_iterative_search": true/false,
            "expected_answer_type": "specifications|comparison|applications|instructions|general"
        }}
        
        Be intelligent about:
        1. Product name variations (ka208, KA208, Kommander KA208)
        2. Typos and fuzzy matching
        3. Series identification (Kommander, Lyzard, etc.)
        4. Technical vs general questions
        5. Comparison requests
        """
        
        try:
            response = self.llm_manager.generate_response(analysis_prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                self.logger.info(f"LLM Query Analysis: {analysis}")
                return analysis
            else:
                self.logger.warning("Could not parse LLM analysis, using fallback")
                return self._fallback_analysis(user_query, fuzzy_matches)
                
        except Exception as e:
            self.logger.error(f"Error in LLM query analysis: {e}")
            return self._fallback_analysis(user_query, fuzzy_matches)
    
    def _fallback_analysis(self, query: str, fuzzy_matches: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        detected_products = [match[0] for match in fuzzy_matches if match[1] > 0.7]
        
        return {
            "intent": "product_search" if detected_products else "general_info",
            "detected_products": detected_products,
            "search_strategies": [{
                "strategy_type": "hybrid",
                "search_terms": [query] + detected_products,
                "filters": {},
                "top_k": 10,
                "confidence_threshold": 0.6,
                "explanation": "Fallback hybrid search"
            }],
            "query_complexity": "moderate",
            "needs_iterative_search": True,
            "expected_answer_type": "general"
        }
    
    def execute_search_strategy(self, strategy: SearchStrategy) -> List[Dict[str, Any]]:
        """Execute a specific search strategy"""
        try:
            if strategy.strategy_type == "exact":
                return self._exact_search(strategy)
            elif strategy.strategy_type == "fuzzy":
                return self._fuzzy_search(strategy)
            elif strategy.strategy_type == "semantic":
                return self._semantic_search(strategy)
            elif strategy.strategy_type == "hybrid":
                return self._hybrid_search(strategy)
            elif strategy.strategy_type == "exploratory":
                return self._exploratory_search(strategy)
            else:
                return self._hybrid_search(strategy)  # Default fallback
                
        except Exception as e:
            self.logger.error(f"Error executing search strategy {strategy.strategy_type}: {e}")
            return []
    
    def _exact_search(self, strategy: SearchStrategy) -> List[Dict[str, Any]]:
        """Exact term matching search"""
        results = []
        for term in strategy.search_terms:
            term_results = self.vector_store.search(
                query=term,
                top_k=strategy.top_k,
                filters=strategy.filters
            )
            results.extend(term_results)
        
        # Remove duplicates and sort by score
        seen_ids = set()
        unique_results = []
        for result in sorted(results, key=lambda x: x['score'], reverse=True):
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
        
        return unique_results[:strategy.top_k]
    
    def _fuzzy_search(self, strategy: SearchStrategy) -> List[Dict[str, Any]]:
        """Fuzzy matching search with expanded terms"""
        expanded_terms = []
        
        for term in strategy.search_terms:
            expanded_terms.append(term)
            # Add fuzzy matches
            fuzzy_matches = self.fuzzy_match_products(term, threshold=0.5)
            for product_id, score in fuzzy_matches:
                if product_id in self.product_knowledge['products']:
                    expanded_terms.extend(self.product_knowledge['products'][product_id]['aliases'])
        
        # Execute search with expanded terms
        strategy.search_terms = list(set(expanded_terms))
        return self._semantic_search(strategy)
    
    def _semantic_search(self, strategy: SearchStrategy) -> List[Dict[str, Any]]:
        """Semantic vector search"""
        combined_query = " ".join(strategy.search_terms)
        return self.vector_store.search(
            query=combined_query,
            top_k=strategy.top_k,
            filters=strategy.filters
        )
    
    def _hybrid_search(self, strategy: SearchStrategy) -> List[Dict[str, Any]]:
        """Hybrid search combining multiple approaches"""
        all_results = []
        
        # Semantic search
        semantic_results = self._semantic_search(strategy)
        all_results.extend([(r, 'semantic') for r in semantic_results])
        
        # Exact matching for product names
        for term in strategy.search_terms:
            exact_results = self.vector_store.search(
                query=f'"{term}"',  # Quoted for exact matching
                top_k=strategy.top_k // 2,
                filters=strategy.filters
            )
            all_results.extend([(r, 'exact') for r in exact_results])
        
        # Score combination and deduplication
        combined_results = self._combine_and_rank_results(all_results)
        return combined_results[:strategy.top_k]
    
    def _exploratory_search(self, strategy: SearchStrategy) -> List[Dict[str, Any]]:
        """Exploratory search for when initial searches fail"""
        # Broader search with relaxed filters
        relaxed_strategy = SearchStrategy(
            strategy_type="semantic",
            search_terms=strategy.search_terms,
            filters={},  # No filters
            top_k=strategy.top_k * 2,
            confidence_threshold=0.3,  # Lower threshold
            explanation="Exploratory search with relaxed criteria"
        )
        
        return self._semantic_search(relaxed_strategy)
    
    def _combine_and_rank_results(self, results_list: List[Tuple[Dict, str]]) -> List[Dict[str, Any]]:
        """Combine and rank results from multiple search strategies"""
        result_scores = {}
        
        for result, strategy_type in results_list:
            result_id = result['id']
            base_score = result['score']
            
            # Weight scores based on strategy type
            if strategy_type == 'exact':
                weighted_score = base_score * 1.5  # Boost exact matches
            elif strategy_type == 'semantic':
                weighted_score = base_score * 1.0
            else:
                weighted_score = base_score * 0.8
            
            if result_id in result_scores:
                # Combine scores (max + bonus for multiple matches)
                result_scores[result_id]['combined_score'] = max(
                    result_scores[result_id]['combined_score'], weighted_score
                ) + (weighted_score * 0.1)  # Small bonus for multiple strategy matches
            else:
                result_scores[result_id] = {
                    'result': result,
                    'combined_score': weighted_score,
                    'strategies': [strategy_type]
                }
        
        # Sort by combined score
        sorted_results = sorted(
            result_scores.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return [item['result'] for item in sorted_results]
    
    def evaluate_results_with_llm(self, query: str, results: List[Dict], analysis: Dict) -> Dict[str, Any]:
        """Let LLM evaluate if results are sufficient or need refinement"""
        
        evaluation_prompt = f"""
        Evaluate these search results for the user query:
        
        USER QUERY: "{query}"
        QUERY ANALYSIS: {json.dumps(analysis, indent=2)}
        
        SEARCH RESULTS ({len(results)} documents):
        {self._format_results_for_llm(results)}
        
        Evaluate and respond with JSON:
        {{
            "results_quality": "excellent|good|fair|poor",
            "coverage_score": 0.0-1.0,
            "relevance_score": 0.0-1.0,
            "completeness_score": 0.0-1.0,
            "needs_refinement": true/false,
            "missing_information": ["what's missing"],
            "refinement_suggestions": [
                {{
                    "strategy_type": "strategy",
                    "search_terms": ["new terms"],
                    "explanation": "why this refinement"
                }}
            ],
            "can_answer": true/false,
            "answer_confidence": 0.0-1.0
        }}
        
        Consider:
        1. Does this answer the user's specific question?
        2. Are the right products/information included?
        3. Is technical information sufficient?
        4. Are comparisons possible if requested?
        """
        
        try:
            response = self.llm_manager.generate_response(evaluation_prompt)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                self.logger.info(f"LLM Result Evaluation: {evaluation}")
                return evaluation
            else:
                return self._fallback_evaluation(results)
                
        except Exception as e:
            self.logger.error(f"Error in LLM result evaluation: {e}")
            return self._fallback_evaluation(results)
    
    def _fallback_evaluation(self, results: List[Dict]) -> Dict[str, Any]:
        """Fallback evaluation when LLM fails"""
        return {
            "results_quality": "fair" if results else "poor",
            "coverage_score": min(len(results) / 5.0, 1.0),
            "relevance_score": 0.7 if results else 0.0,
            "completeness_score": 0.6 if results else 0.0,
            "needs_refinement": len(results) < 3,
            "missing_information": [],
            "refinement_suggestions": [],
            "can_answer": len(results) > 0,
            "answer_confidence": 0.6 if results else 0.1
        }
    
    def _format_results_for_llm(self, results: List[Dict], max_results: int = 5) -> str:
        """Format results for LLM evaluation"""
        formatted = []
        for i, result in enumerate(results[:max_results]):
            formatted.append(f"""
            Document {i+1}:
            - Content: {result.get('content', '')[:200]}...
            - Score: {result.get('score', 0):.3f}
            - Metadata: {result.get('metadata', {})}
            """)
        return "\n".join(formatted)
    
    def synthesize_final_answer(self, query: str, all_results: List[Dict], analysis: Dict) -> str:
        """Generate final answer using all collected information"""
        
        synthesis_prompt = f"""
        Generate a comprehensive answer for this K-Array technical query:
        
        USER QUERY: "{query}"
        QUERY INTENT: {analysis.get('intent', 'general')}
        EXPECTED ANSWER TYPE: {analysis.get('expected_answer_type', 'general')}
        
        RETRIEVED INFORMATION:
        {self._format_results_for_synthesis(all_results)}
        
        GUIDELINES:
        1. Provide accurate, specific technical information
        2. Include exact specifications with source attribution
        3. Use professional K-Array terminology
        4. If comparing products, create clear comparisons
        5. If information is missing, acknowledge it specifically
        6. Structure the answer logically
        7. Include relevant model numbers and series information
        
        Answer format:
        - Start with direct answer to the question
        - Provide detailed specifications if requested
        - Include sources and attributions
        - Suggest related products/information if relevant
        """
        
        try:
            response = self.llm_manager.generate_response(synthesis_prompt)
            return response.strip()
        except Exception as e:
            self.logger.error(f"Error in answer synthesis: {e}")
            return "I apologize, but I encountered an error while generating the response. Please try rephrasing your question."
    
    def _format_results_for_synthesis(self, results: List[Dict]) -> str:
        """Format all results for final synthesis"""
        if not results:
            return "No relevant information found."
        
        formatted_sections = []
        for i, result in enumerate(results):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            
            section = f"""
            Source {i+1} (Relevance: {score:.3f}):
            Content: {content}
            Product/Category: {metadata.get('category', 'Unknown')}
            Model: {metadata.get('model', 'Unknown')}
            Source File: {metadata.get('source_file', 'Unknown')}
            """
            formatted_sections.append(section)
        
        return "\n".join(formatted_sections)
    
    def process_query(self, user_query: str, max_iterations: int = 3) -> str:
        """Main orchestration method - LLM-driven multi-stage RAG"""
        
        self.logger.info(f"Processing query: {user_query}")
        
        # Stage 1: LLM Query Analysis
        analysis = self.analyze_query_with_llm(user_query, self.conversation_context)
        
        all_results = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"RAG Iteration {iteration}")
            
            # Stage 2: Execute Search Strategies
            for strategy_config in analysis.get('search_strategies', []):
                strategy = SearchStrategy(**strategy_config)
                results = self.execute_search_strategy(strategy)
                all_results.extend(results)
            
            # Remove duplicates
            seen_ids = set()
            unique_results = []
            for result in all_results:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    unique_results.append(result)
            all_results = unique_results
            
            # Stage 3: LLM Result Evaluation
            evaluation = self.evaluate_results_with_llm(user_query, all_results, analysis)
            
            # Stage 4: Check if we need more iterations
            if evaluation.get('can_answer', False) and not evaluation.get('needs_refinement', True):
                break
            
            if iteration < max_iterations and evaluation.get('needs_refinement', True):
                # Stage 5: LLM-suggested refinement
                refinement_strategies = evaluation.get('refinement_suggestions', [])
                if refinement_strategies:
                    self.logger.info(f"Refining search with {len(refinement_strategies)} additional strategies")
                    analysis['search_strategies'] = refinement_strategies
                else:
                    break
        
        # Stage 6: Final Synthesis
        final_answer = self.synthesize_final_answer(user_query, all_results, analysis)
        
        # Update conversation context
        self.conversation_context.append({
            'query': user_query,
            'analysis': analysis,
            'results_count': len(all_results),
            'iterations': iteration
        })
        
        # Keep only last 10 interactions
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
        
        return final_answer


if __name__ == "__main__":
    # Test the orchestrator
    from src.local_vector_store import LocalVectorStore
    from src.llm_manager import LLMManager
    
    # Initialize components
    vector_store = LocalVectorStore()
    llm_manager = LLMManager()
    orchestrator = IntelligentRAGOrchestrator(vector_store, llm_manager)
    
    # Test queries
    test_queries = [
        "mi dai informazioni sul K framework 3?",
        "mi dai informazioni sul ka208", 
        "Quali sono le specifiche del Kommander KA104?",
        "Differenze tra serie Lyzard e Vyper"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        answer = orchestrator.process_query(query)
        print(answer)