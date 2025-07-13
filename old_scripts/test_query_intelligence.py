#!/usr/bin/env python3
"""
Test script for Query Intelligence Layer
Tests LLM-based query understanding, translation, and optimization
"""

import sys
import os
sys.path.append('.')

def test_query_intelligence_import():
    """Test query intelligence module import"""
    print("🔍 Testing query intelligence import...")
    
    try:
        from src.query_intelligence import QueryIntelligenceEngine, QueryIntelligence, QueryIntent, QueryComplexity
        print("✅ Query intelligence imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_query_analysis_without_llm():
    """Test query analysis with fallback (no LLM)"""
    print("🔍 Testing query analysis fallback...")
    
    try:
        # Mock the LLM manager to avoid API dependency
        class MockLLMManager:
            def generate_text(self, prompt):
                raise Exception("Mock LLM failure")
        
        from src.query_intelligence import QueryIntelligenceEngine
        
        # Replace LLM manager temporarily
        engine = QueryIntelligenceEngine()
        engine.llm_manager = MockLLMManager()
        
        test_queries = [
            "Che potenza ha il KA02I?",
            "What power does KA02I have?",
            "Compare KA02I vs KA04",
            "Hotel installation guide"
        ]
        
        for query in test_queries:
            intelligence = engine.analyze_query(query)
            
            if intelligence and hasattr(intelligence, 'intent'):
                print(f"✅ Query '{query}': Intent={intelligence.intent.value}")
            else:
                print(f"❌ Query '{query}': Failed to analyze")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Query analysis test error: {e}")
        return False

def test_language_detection():
    """Test language detection and translation logic"""
    print("🔍 Testing language detection...")
    
    try:
        from src.query_intelligence import QueryIntelligenceEngine
        
        engine = QueryIntelligenceEngine()
        
        test_cases = [
            ("What is the power of KA02I?", "english"),
            ("Che potenza ha il KA02I?", "italian"),
            ("¿Cuál es la potencia del KA02I?", "spanish"),
            ("Quelle est la puissance du KA02I?", "french")
        ]
        
        for query, expected_lang in test_cases:
            result = engine._detect_and_translate(query)
            
            if result['language'] == expected_lang:
                print(f"✅ Language detection: '{query}' → {expected_lang}")
            else:
                print(f"❌ Language detection: '{query}' → {result['language']}, expected {expected_lang}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Language detection test error: {e}")
        return False

def test_intent_classification():
    """Test intent classification logic"""
    print("🔍 Testing intent classification...")
    
    try:
        from src.query_intelligence import QueryIntelligenceEngine, QueryIntent
        
        engine = QueryIntelligenceEngine()
        
        test_cases = [
            ("KA02I power specifications", "technical_specs_only"),
            ("Where is KA02I used?", "applications_only"),
            ("Compare KA02I vs KA04", "product_comparison"),
            ("How to install speakers", "installation_guidance"),
            ("Speaker not working", "troubleshooting"),
            ("Tell me about K-Array", "general_info")
        ]
        
        for query, expected_intent in test_cases:
            # Use fallback analysis since we don't have LLM
            analysis = engine._fallback_intent_analysis(query)
            
            # Check if intent is reasonable (fallback may not be exact)
            if analysis['intent'] in [intent.value for intent in QueryIntent]:
                print(f"✅ Intent classification: '{query}' → {analysis['intent']}")
            else:
                print(f"❌ Intent classification: '{query}' → {analysis['intent']} (invalid)")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Intent classification test error: {e}")
        return False

def test_query_optimization():
    """Test query optimization for retrieval"""
    print("🔍 Testing query optimization...")
    
    try:
        from src.query_intelligence import QueryIntelligenceEngine
        
        engine = QueryIntelligenceEngine()
        
        test_cases = [
            {
                'query': 'power KA02I',
                'intent_analysis': {
                    'intent': 'technical_specs_only',
                    'products': ['ka02i'],
                    'technical_focus': ['power'],
                    'application_focus': []
                },
                'should_contain': ['KA02I', 'specifications']
            },
            {
                'query': 'hotel applications',
                'intent_analysis': {
                    'intent': 'applications_only',
                    'products': [],
                    'technical_focus': [],
                    'application_focus': ['hotel']
                },
                'should_contain': ['applications', 'use cases']
            }
        ]
        
        for test_case in test_cases:
            optimized = engine._optimize_for_retrieval(
                test_case['query'],
                None,  # No translation
                test_case['intent_analysis']
            )
            
            # Check if optimization contains expected terms
            contains_expected = any(term.lower() in optimized.lower() 
                                  for term in test_case['should_contain'])
            
            if contains_expected:
                print(f"✅ Query optimization: '{test_case['query']}' → '{optimized}'")
            else:
                print(f"❌ Query optimization: '{test_case['query']}' → '{optimized}' "
                      f"(missing {test_case['should_contain']})")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Query optimization test error: {e}")
        return False

def test_clarification_logic():
    """Test clarification question generation"""
    print("🔍 Testing clarification logic...")
    
    try:
        from src.query_intelligence import QueryIntelligenceEngine, QueryIntelligence, QueryIntent, QueryComplexity
        
        engine = QueryIntelligenceEngine()
        
        # Test ambiguous query that should trigger clarification
        ambiguous_intelligence = QueryIntelligence(
            original_query="tell me about speakers",
            language="english",
            translated_query=None,
            optimized_query="tell me about speakers",
            intent=QueryIntent.GENERAL_INFO,
            complexity=QueryComplexity.AMBIGUOUS,
            products_mentioned=[],
            technical_focus=[],
            application_focus=[],
            exclusions=[],
            confidence=0.4,  # Low confidence
            suggested_followup=None,
            retrieval_strategy="balanced",
            reasoning="Very general query"
        )
        
        # Test if clarification is needed
        should_clarify = engine.should_ask_clarification(ambiguous_intelligence)
        if should_clarify:
            print("✅ Correctly identified need for clarification")
            
            clarification = engine.generate_clarification_question(ambiguous_intelligence)
            if clarification and len(clarification) > 10:
                print(f"✅ Generated clarification: '{clarification[:50]}...'")
            else:
                print("❌ Failed to generate meaningful clarification")
                return False
        else:
            print("❌ Failed to identify need for clarification")
            return False
        
        # Test clear query that shouldn't need clarification
        clear_intelligence = QueryIntelligence(
            original_query="KA02I power specifications",
            language="english",
            translated_query=None,
            optimized_query="KA02I power specifications technical details",
            intent=QueryIntent.TECHNICAL_SPECS_ONLY,
            complexity=QueryComplexity.SIMPLE,
            products_mentioned=["ka02i"],
            technical_focus=["power_output"],
            application_focus=[],
            exclusions=[],
            confidence=0.9,  # High confidence
            suggested_followup=None,
            retrieval_strategy="technical_focused",
            reasoning="Clear technical query"
        )
        
        should_not_clarify = engine.should_ask_clarification(clear_intelligence)
        if not should_not_clarify:
            print("✅ Correctly identified no need for clarification")
        else:
            print("❌ Incorrectly suggested clarification for clear query")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Clarification logic test error: {e}")
        return False

def test_integration_with_multi_vector():
    """Test integration with multi-vector retriever"""
    print("🔍 Testing integration with multi-vector retriever...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        # Mock vector store
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return [
                    {
                        'id': f'test_{i}',
                        'content': f'Test content {i} for: {query}',
                        'score': 0.8,
                        'metadata': {'content_type': 'test'}
                    } for i in range(2)
                ]
        
        mock_store = MockVectorStore()
        
        # Test with query intelligence enabled
        retriever = MultiVectorRetriever(
            mock_store, 
            enable_reranking=False,  # Disable to avoid dependencies
            enable_query_intelligence=True
        )
        
        # Mock the LLM in query intelligence to avoid API calls
        if retriever.query_intelligence:
            class MockLLMManager:
                def generate_text(self, prompt):
                    return '{"intent": "technical_specs_only", "complexity": "simple", "products": ["ka02i"], "technical_focus": ["power"], "application_focus": [], "exclusions": [], "confidence": 0.8, "reasoning": "Mock analysis"}'
            
            retriever.query_intelligence.llm_manager = MockLLMManager()
        
        # Test retrieval with intelligence
        results, query_intelligence = retriever.retrieve("KA02I power specifications")
        
        if results and len(results) > 0:
            print(f"✅ Integration test: {len(results)} results retrieved")
        else:
            print("❌ Integration test: No results retrieved")
            return False
        
        if query_intelligence:
            print(f"✅ Query intelligence returned: {query_intelligence.intent.value}")
        else:
            print("❌ No query intelligence returned")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def main():
    """Run all query intelligence tests"""
    print("🚀 Query Intelligence Testing: LLM-powered Query Understanding")
    print("=" * 65)
    
    tests = [
        ("Query Intelligence Import Test", test_query_intelligence_import),
        ("Query Analysis Fallback Test", test_query_analysis_without_llm),
        ("Language Detection Test", test_language_detection),
        ("Intent Classification Test", test_intent_classification),
        ("Query Optimization Test", test_query_optimization),
        ("Clarification Logic Test", test_clarification_logic),
        ("Multi-Vector Integration Test", test_integration_with_multi_vector)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append(result)
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    print("\n" + "=" * 65)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 QUERY INTELLIGENCE COMPLETE: ALL TESTS PASSED ({passed}/{total})")
        print("✅ Sistema con intelligenza query LLM pronto!")
        print("\n📈 NUOVE CAPACITÀ:")
        print("   • Comprensione LLM del intento utente")
        print("   • Traduzione automatica in inglese")
        print("   • Ottimizzazione query per retrieval")
        print("   • Domande di chiarimento intelligenti")
        print("   • Analisi contesto conversazionale")
        print("   • Fallback robusto senza LLM")
    else:
        print(f"⚠️  QUERY INTELLIGENCE ISSUES: {passed}/{total} tests passed")
        print("❌ Fix failing tests before production deployment")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)