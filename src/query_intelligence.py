#!/usr/bin/env python3
"""
Query Intelligence Layer for K-Array Chat System
Advanced query understanding, translation, and optimization using LLM
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from src.llm_manager import LLMManager
from src.dynamic_config import dynamic_config


class QueryIntent(Enum):
    """Refined query intent categories"""
    TECHNICAL_SPECS_ONLY = "technical_specs_only"
    APPLICATIONS_ONLY = "applications_only"
    PRODUCT_COMPARISON = "product_comparison"
    INSTALLATION_GUIDANCE = "installation_guidance"
    TROUBLESHOOTING = "troubleshooting"
    GENERAL_INFO = "general_info"
    PURCHASE_DECISION = "purchase_decision"
    COMPATIBILITY_CHECK = "compatibility_check"


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"           # Single product, single attribute
    MODERATE = "moderate"       # Multiple attributes or basic comparison
    COMPLEX = "complex"         # Multiple products, complex requirements
    AMBIGUOUS = "ambiguous"     # Unclear intent, needs clarification


@dataclass
class QueryIntelligence:
    """Comprehensive query understanding result"""
    original_query: str
    language: str
    translated_query: Optional[str]
    optimized_query: str
    intent: QueryIntent
    complexity: QueryComplexity
    products_mentioned: List[str]
    technical_focus: List[str]  # Power, dimensions, frequency, etc.
    application_focus: List[str]  # Hotel, restaurant, theater, etc.
    exclusions: List[str]  # What user explicitly doesn't want
    confidence: float
    suggested_followup: Optional[str]
    retrieval_strategy: str
    reasoning: str


class QueryIntelligenceEngine:
    """Advanced query understanding and optimization engine"""
    
    def __init__(self, llm_provider: str = "gemini"):
        self.llm_manager = LLMManager(llm_provider)
        self.setup_logging()
        
        # Dynamic domain knowledge - will be populated by LLM when needed
        self._domain_knowledge_cache = {
            'products': None,
            'technical_categories': None,
            'application_categories': None,
            'last_updated': None
        }
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def get_dynamic_domain_knowledge(self) -> Dict[str, Any]:
        """Get K-Array domain knowledge dynamically from LLM or config"""
        
        # First try to load from configuration files
        config_knowledge = dynamic_config.get_domain_knowledge()
        if config_knowledge and self._is_knowledge_fresh(config_knowledge):
            self.logger.info("Using domain knowledge from configuration file")
            self._domain_knowledge_cache = {
                'products': config_knowledge.get('product_series', {}),
                'technical_categories': config_knowledge.get('technical_categories', []),
                'application_categories': config_knowledge.get('application_categories', []),
                'variations': config_knowledge.get('common_variations', {}),
                'last_updated': config_knowledge.get('last_updated', datetime.now().isoformat())
            }
            return self._domain_knowledge_cache
        
        # If config knowledge is stale or missing, get from LLM
        try:
            knowledge_prompt = """
            You are an expert on K-Array professional audio equipment. Provide comprehensive domain knowledge in JSON format:

            {
                "product_series": {
                    "kommander": ["list of kommander models like ka02i, ka04, etc."],
                    "lyzard": ["list of lyzard models"],
                    "vyper": ["list of vyper models"],
                    "python": ["list of python models"],
                    "firenze": ["list of firenze models"],
                    "azimut": ["list of azimut models"],
                    "other_series": ["any other K-Array series you know"]
                },
                "technical_categories": [
                    "list of technical specifications categories like power_output, frequency_response, etc."
                ],
                "application_categories": [
                    "list of application contexts like hospitality, retail, theaters, etc."
                ],
                "common_variations": {
                    "product_name_variations": {
                        "ka02i": ["ka-02i", "ka 02i", "kommander ka02i"],
                        "other_products": "similar variations"
                    }
                }
            }

            Base your response on your knowledge of K-Array products and audio industry standards.
            Include as many real K-Array products and categories as you know.
            
            Response:
            """
            
            response = self.llm_manager.generate_text(knowledge_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                knowledge = json.loads(json_str)
                
                # Cache the knowledge
                updated_knowledge = {
                    'product_series': knowledge.get('product_series', {}),
                    'technical_categories': knowledge.get('technical_categories', []),
                    'application_categories': knowledge.get('application_categories', []),
                    'common_variations': knowledge.get('common_variations', {}),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Save to configuration for future use
                dynamic_config.save_domain_knowledge(updated_knowledge)
                
                self._domain_knowledge_cache = {
                    'products': updated_knowledge['product_series'],
                    'technical_categories': updated_knowledge['technical_categories'],
                    'application_categories': updated_knowledge['application_categories'],
                    'variations': updated_knowledge['common_variations'],
                    'last_updated': updated_knowledge['last_updated']
                }
                
                self.logger.info("Dynamic domain knowledge updated from LLM and saved to config")
                return self._domain_knowledge_cache
            else:
                raise ValueError("No valid JSON found in LLM response")
                
        except Exception as e:
            self.logger.warning(f"Dynamic knowledge extraction failed: {e}, using fallback")
            return self._get_fallback_domain_knowledge()
    
    def _is_knowledge_fresh(self, knowledge: Dict[str, Any]) -> bool:
        """Check if knowledge from config is still fresh"""
        
        if not knowledge.get('last_updated'):
            return False
        
        try:
            last_update = datetime.fromisoformat(knowledge['last_updated'])
            cache_ttl = dynamic_config.cache_config.domain_knowledge_ttl_hours
            hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
            return hours_since_update < cache_ttl
        except (ValueError, TypeError):
            return False
    
    def _get_fallback_domain_knowledge(self) -> Dict[str, Any]:
        """Fallback domain knowledge when LLM fails"""
        
        return {
            'products': {
                'kommander': ['ka02i', 'ka04', 'ka08', 'ka102', 'ka104'],
                'lyzard': ['kz1', 'kz7', 'kz14', 'kz26'],
                'vyper': ['kv25', 'kv52'],
                'python': ['kp102', 'kp52', 'kp25'],
                'firenze': ['ks4p', 'ks7p', 'ks10p'],
                'azimut': ['kamut2l', 'kamut2v25']
            },
            'technical_categories': [
                'power_output', 'frequency_response', 'dimensions', 'weight',
                'impedance', 'spl', 'connectivity', 'mounting', 'materials'
            ],
            'application_categories': [
                'hospitality', 'retail', 'museums', 'theaters', 'restaurants',
                'hotels', 'fitness', 'marine', 'worship', 'corporate'
            ],
            'variations': {},
            'last_updated': 'fallback'
        }
    
    def get_domain_knowledge(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get domain knowledge with intelligent caching strategy"""
        
        # Check if we need to refresh based on various criteria
        needs_refresh = (
            force_refresh or 
            self._domain_knowledge_cache['products'] is None or
            self._domain_knowledge_cache['last_updated'] is None or
            self._domain_knowledge_cache['last_updated'] == 'fallback' or
            self._is_knowledge_stale()
        )
        
        if needs_refresh:
            return self.get_dynamic_domain_knowledge()
        
        return self._domain_knowledge_cache
    
    def _is_knowledge_stale(self) -> bool:
        """Check if cached domain knowledge is stale"""
        
        if not self._domain_knowledge_cache['last_updated'] or self._domain_knowledge_cache['last_updated'] == 'fallback':
            return True
        
        try:
            last_update = datetime.fromisoformat(self._domain_knowledge_cache['last_updated'])
            # Use configurable TTL
            cache_ttl = dynamic_config.cache_config.domain_knowledge_ttl_hours
            hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
            return hours_since_update > cache_ttl
        except (ValueError, TypeError):
            return True
    
    def update_domain_knowledge_from_query(self, query: str, extracted_entities: Dict[str, Any]):
        """Learn new domain knowledge from user queries"""
        
        # Extract new products or categories mentioned in queries
        new_products = []
        new_tech_categories = []
        new_app_categories = []
        
        # Simple pattern matching for unknown products
        product_patterns = re.findall(r'k[a-z]*[0-9]+[a-z]*', query.lower())
        for product in product_patterns:
            # Check if it's a new product
            known_products = []
            for models in self._domain_knowledge_cache.get('products', {}).values():
                known_products.extend(models)
            
            if product not in [p.lower() for p in known_products]:
                new_products.append(product.upper())
        
        # If we found new knowledge, consider refreshing
        if new_products or new_tech_categories or new_app_categories:
            self.logger.info(f"Discovered potentially new domain knowledge: {new_products}")
            # Could trigger a background refresh or store for next update
            return {
                'new_products': new_products,
                'new_tech_categories': new_tech_categories,
                'new_app_categories': new_app_categories
            }
        
        return None
    
    def analyze_query(self, query: str, conversation_history: Optional[List[Dict]] = None) -> QueryIntelligence:
        """
        Comprehensive query analysis using LLM intelligence
        
        Args:
            query: User's original query
            conversation_history: Previous conversation context
            
        Returns:
            QueryIntelligence object with complete understanding
        """
        
        self.logger.info(f"Analyzing query: '{query[:100]}...'")
        
        try:
            # Step 1: Language detection and translation
            language_result = self._detect_and_translate(query)
            
            # Step 2: LLM-powered intent analysis
            intent_analysis = self._analyze_intent_with_llm(
                query, 
                language_result['translated_query'],
                conversation_history
            )
            
            # Step 3: Query optimization for retrieval
            optimized_query = self._optimize_for_retrieval(
                query,
                language_result['translated_query'],
                intent_analysis
            )
            
            # Step 4: Generate retrieval strategy
            retrieval_strategy = self._determine_retrieval_strategy(intent_analysis)
            
            # Step 5: Create comprehensive intelligence result
            intelligence = QueryIntelligence(
                original_query=query,
                language=language_result['language'],
                translated_query=language_result['translated_query'],
                optimized_query=optimized_query,
                intent=QueryIntent(intent_analysis['intent']),
                complexity=QueryComplexity(intent_analysis['complexity']),
                products_mentioned=intent_analysis['products'],
                technical_focus=intent_analysis['technical_focus'],
                application_focus=intent_analysis['application_focus'],
                exclusions=intent_analysis['exclusions'],
                confidence=intent_analysis['confidence'],
                suggested_followup=intent_analysis.get('suggested_followup'),
                retrieval_strategy=retrieval_strategy,
                reasoning=intent_analysis['reasoning']
            )
            
            self.logger.info(f"Query analysis complete: Intent={intelligence.intent.value}, "
                           f"Complexity={intelligence.complexity.value}, Confidence={intelligence.confidence:.2f}")
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error in query analysis: {str(e)}")
            # Return fallback analysis
            return self._create_fallback_intelligence(query)
    
    def _detect_and_translate(self, query: str) -> Dict[str, Any]:
        """Dynamically detect language and translate using LLM"""
        
        # LLM-powered language detection and translation
        detection_prompt = f"""
        Analyze this query and detect its language. Then, if it's not English, translate it to English.
        
        Query: "{query}"
        
        Provide a JSON response with:
        {{
            "detected_language": "english/italian/spanish/french/german/portuguese/other",
            "confidence": 0.0-1.0,
            "translation_needed": true/false,
            "english_translation": "translation here if needed, or null if already English"
        }}
        
        Rules:
        - If already in English, set translation_needed: false
        - Keep K-Array product names unchanged (KA02I, Kommander, etc.)
        - Keep technical terms in English
        - Maintain the query's intent and specificity
        
        Response:
        """
        
        try:
            response = self.llm_manager.generate_text(detection_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                language = result.get('detected_language', 'english')
                translation_needed = result.get('translation_needed', False)
                translated = result.get('english_translation')
                
                return {
                    'language': language,
                    'translated_query': translated if translation_needed else None,
                    'confidence': result.get('confidence', 0.8)
                }
            else:
                raise ValueError("No valid JSON found in LLM response")
                
        except Exception as e:
            self.logger.warning(f"LLM language detection failed: {e}, using fallback")
            return self._fallback_language_detection(query)
    
    def _fallback_language_detection(self, query: str) -> Dict[str, Any]:
        """Fallback language detection when LLM fails"""
        
        query_lower = query.lower()
        
        # Minimal fallback patterns
        if any(marker in query_lower for marker in ['¿', '¡', 'cuál', 'cómo']):
            language = 'spanish'
        elif any(word in query_lower for word in ['è', 'che', 'potenza', 'della']):
            language = 'italian'
        elif any(word in query_lower for word in ['est', 'du', 'quelle', 'puissance']):
            language = 'french'
        else:
            language = 'english'
        
        return {
            'language': language,
            'translated_query': None,  # No translation in fallback
            'confidence': 0.6
        }
    
    def _analyze_intent_with_llm(self, 
                                original_query: str, 
                                translated_query: Optional[str],
                                conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Advanced intent analysis using LLM reasoning with dynamic domain knowledge"""
        
        analysis_query = translated_query or original_query
        
        # Get dynamic domain knowledge
        domain_knowledge = self.get_domain_knowledge()
        
        # Build context from conversation
        context = ""
        if conversation_history:
            recent_context = conversation_history[-3:]  # Last 3 exchanges
            context = "Previous conversation context:\n"
            for msg in recent_context:
                context += f"- {msg.get('role', 'user')}: {msg.get('content', '')[:100]}...\n"
            context += "\n"
        
        # Build domain knowledge context
        products_context = ""
        for series, models in domain_knowledge.get('products', {}).items():
            products_context += f"- {series}: {', '.join(models)}\n"
        
        tech_categories = domain_knowledge.get('technical_categories', [])
        app_categories = domain_knowledge.get('application_categories', [])
        
        # Dynamic detailed prompt for intent analysis
        intent_prompt = f"""
        You are an expert in K-Array professional audio equipment. Analyze this query with deep understanding:
        
        {context}Current Query: "{analysis_query}"
        
        K-Array Product Knowledge:
        {products_context}
        
        Technical Categories: {', '.join(tech_categories)}
        Application Categories: {', '.join(app_categories)}
        
        Analyze and provide a JSON response with these fields:
        
        1. "intent": Choose the most specific intent:
           - "technical_specs_only": User wants only technical specifications, no applications
           - "applications_only": User wants only use cases/installations, no technical details
           - "product_comparison": Comparing multiple products or series
           - "installation_guidance": How to install, setup, configure
           - "troubleshooting": Problem-solving, issues, not working
           - "general_info": General information about products/company
           - "purchase_decision": Help choosing right product for specific need
           - "compatibility_check": Whether products work together
        
        2. "complexity": 
           - "simple": Single product, single question
           - "moderate": Multiple aspects or basic comparison
           - "complex": Multiple products, complex requirements
           - "ambiguous": Unclear intent, needs clarification
        
        3. "products": List of K-Array products mentioned (exact names from the product knowledge above)
        
        4. "technical_focus": Technical aspects user cares about (from technical categories above)
        
        5. "application_focus": Application contexts mentioned (from application categories above)
        
        6. "exclusions": What user explicitly DOESN'T want
        
        7. "confidence": Float 0.0-1.0 for analysis confidence
        
        8. "suggested_followup": If ambiguous, suggest a clarifying question
        
        9. "reasoning": Brief explanation of your analysis
        
        Focus on understanding what the user REALLY wants using the provided domain knowledge.
        Use the exact product names and categories from the knowledge base above.
        
        Respond with valid JSON only:
        """
        
        try:
            response = self.llm_manager.generate_text(intent_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                # Validate and set defaults
                analysis['intent'] = analysis.get('intent', 'general_info')
                analysis['complexity'] = analysis.get('complexity', 'moderate')
                analysis['products'] = analysis.get('products', [])
                analysis['technical_focus'] = analysis.get('technical_focus', [])
                analysis['application_focus'] = analysis.get('application_focus', [])
                analysis['exclusions'] = analysis.get('exclusions', [])
                analysis['confidence'] = float(analysis.get('confidence', 0.7))
                analysis['reasoning'] = analysis.get('reasoning', 'LLM analysis completed')
                
                return analysis
            else:
                raise ValueError("No valid JSON found in LLM response")
                
        except Exception as e:
            self.logger.warning(f"LLM intent analysis failed: {e}")
            return self._fallback_intent_analysis(analysis_query)
    
    def _fallback_intent_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback intent analysis using dynamic domain knowledge"""
        
        query_lower = query.lower()
        
        # Get dynamic domain knowledge
        domain_knowledge = self.get_domain_knowledge()
        
        # Extract keywords dynamically
        tech_keywords = domain_knowledge.get('technical_categories', [])
        app_keywords = domain_knowledge.get('application_categories', [])
        
        # Add common heuristic keywords as fallback
        tech_keywords.extend(['power', 'watt', 'frequency', 'hz', 'spl', 'db', 'spec', 'dimension'])
        app_keywords.extend(['hotel', 'restaurant', 'install', 'use', 'application', 'where'])
        comparison_keywords = ['vs', 'versus', 'compare', 'difference', 'better']
        
        # Find products dynamically
        products = []
        product_series = domain_knowledge.get('products', {})
        for series, models in product_series.items():
            if series in query_lower:
                products.append(series)
            for model in models:
                if model.lower() in query_lower:
                    products.append(model)
        
        # Determine intent
        if any(word in query_lower for word in comparison_keywords):
            intent = 'product_comparison'
        elif any(word in query_lower for word in tech_keywords) and not any(word in query_lower for word in app_keywords):
            intent = 'technical_specs_only'
        elif any(word in query_lower for word in app_keywords) and not any(word in query_lower for word in tech_keywords):
            intent = 'applications_only'
        else:
            intent = 'general_info'
        
        return {
            'intent': intent,
            'complexity': 'moderate',
            'products': products,
            'technical_focus': [kw for kw in tech_keywords if kw in query_lower],
            'application_focus': [kw for kw in app_keywords if kw in query_lower],
            'exclusions': [],
            'confidence': 0.6,
            'reasoning': 'Fallback analysis with dynamic domain knowledge'
        }
    
    def _optimize_for_retrieval(self, 
                               original_query: str,
                               translated_query: Optional[str],
                               intent_analysis: Dict[str, Any]) -> str:
        """Optimize query for retrieval based on intent analysis"""
        
        base_query = translated_query or original_query
        intent = intent_analysis['intent']
        
        # Intent-specific optimization
        optimization_rules = {
            'technical_specs_only': [
                'specifications', 'technical details', 'specs',
                'power output', 'frequency response', 'dimensions'
            ],
            'applications_only': [
                'applications', 'use cases', 'installations',
                'suitable for', 'recommended for'
            ],
            'product_comparison': [
                'comparison', 'differences', 'versus',
                'specifications comparison'
            ],
            'installation_guidance': [
                'installation', 'setup', 'mounting',
                'configuration', 'how to install'
            ]
        }
        
        # Add intent-specific terms
        if intent in optimization_rules:
            optimization_terms = optimization_rules[intent]
            optimized = f"{base_query} {' '.join(optimization_terms[:2])}"
        else:
            optimized = base_query
        
        # Add product-specific optimization
        products = intent_analysis.get('products', [])
        if products:
            main_product = products[0]
            optimized = f"{main_product} {optimized}"
        
        return optimized.strip()
    
    def _determine_retrieval_strategy(self, intent_analysis: Dict[str, Any]) -> str:
        """Determine optimal retrieval strategy configuration"""
        
        intent = intent_analysis['intent']
        complexity = intent_analysis['complexity']
        
        # Strategy mapping based on intent
        strategy_map = {
            'technical_specs_only': 'technical_focused',
            'applications_only': 'application_focused', 
            'product_comparison': 'comparison_focused',
            'installation_guidance': 'guidance_focused',
            'troubleshooting': 'problem_solving_focused',
            'purchase_decision': 'decision_support_focused',
            'compatibility_check': 'compatibility_focused',
            'general_info': 'balanced'
        }
        
        base_strategy = strategy_map.get(intent, 'balanced')
        
        # Adjust for complexity
        if complexity == 'complex':
            return f"{base_strategy}_comprehensive"
        elif complexity == 'simple':
            return f"{base_strategy}_focused"
        else:
            return base_strategy
    
    def _create_fallback_intelligence(self, query: str) -> QueryIntelligence:
        """Create fallback intelligence when LLM analysis fails"""
        
        return QueryIntelligence(
            original_query=query,
            language='unknown',
            translated_query=None,
            optimized_query=query,
            intent=QueryIntent.GENERAL_INFO,
            complexity=QueryComplexity.MODERATE,
            products_mentioned=[],
            technical_focus=[],
            application_focus=[],
            exclusions=[],
            confidence=0.5,
            suggested_followup=None,
            retrieval_strategy='balanced',
            reasoning='Fallback analysis due to LLM failure'
        )
    
    def should_ask_clarification(self, intelligence: QueryIntelligence) -> bool:
        """Determine if we should ask for clarification before retrieval"""
        
        return (
            intelligence.complexity == QueryComplexity.AMBIGUOUS or
            intelligence.confidence < 0.6 or
            (intelligence.intent == QueryIntent.GENERAL_INFO and 
             len(intelligence.products_mentioned) == 0 and
             len(intelligence.technical_focus) == 0 and
             len(intelligence.application_focus) == 0)
        )
    
    def generate_clarification_question(self, intelligence: QueryIntelligence) -> str:
        """Generate intelligent clarification question"""
        
        if intelligence.suggested_followup:
            return intelligence.suggested_followup
        
        # Generate based on ambiguity
        if not intelligence.products_mentioned:
            return "Quale prodotto o serie K-Array ti interessa? (es. Kommander, Lyzard, Firenze)"
        
        if intelligence.intent == QueryIntent.GENERAL_INFO:
            return "Cosa ti interessa sapere specificatamente? Le specifiche tecniche o le applicazioni d'uso?"
        
        return "Puoi essere più specifico su cosa stai cercando?"


if __name__ == "__main__":
    # Test the query intelligence engine
    try:
        engine = QueryIntelligenceEngine()
        
        test_queries = [
            "Che potenza ha il KA02I?",
            "Where is the Kommander series typically used?",
            "Compare KA02I vs KA04 specifications",
            "Need help installing speakers in hotel"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            intelligence = engine.analyze_query(query)
            print(f"Intent: {intelligence.intent.value}")
            print(f"Optimized: '{intelligence.optimized_query}'")
            print(f"Strategy: {intelligence.retrieval_strategy}")
            print(f"Confidence: {intelligence.confidence:.2f}")
            
    except Exception as e:
        print(f"❌ Error testing query intelligence: {e}")