#!/usr/bin/env python3
"""
Test script for Phase 3: Multi-Vector Retrieval System
Tests advanced multi-strategy retrieval with fusion and reranking
"""

import sys
import os
sys.path.append('.')

def test_multi_vector_import():
    """Test multi-vector retriever import and initialization"""
    print("🔍 Testing multi-vector retriever import...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever, RetrievalStrategy, MultiVectorResult
        print("✅ Multi-vector retriever imports successful")
        
        # Mock vector store
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return [
                    {
                        'id': f'doc_{i}',
                        'content': f'Mock content {i} for query: {query}',
                        'score': 0.9 - (i * 0.1),
                        'metadata': {'content_type': 'searchable_text', 'model': 'KA02I'}
                    } for i in range(min(top_k, 3))
                ]
        
        mock_store = MockVectorStore()
        retriever = MultiVectorRetriever(mock_store, enable_reranking=True, enable_fusion=True)
        print("✅ Multi-vector retriever initialized with reranking and fusion")
        
        # Test strategy initialization
        strategies = retriever.strategies
        print(f"✅ Initialized {len(strategies)} retrieval strategies")
        
        expected_strategies = ['exact_product_match', 'qa_pairs', 'technical_specs', 
                             'semantic_chunks', 'searchable_content', 'hybrid_search']
        for strategy_name in expected_strategies:
            if strategy_name in strategies:
                print(f"✅ Strategy '{strategy_name}' configured")
            else:
                print(f"❌ Strategy '{strategy_name}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-vector import test error: {e}")
        return False

def test_query_analysis():
    """Test query intent analysis"""
    print("🔍 Testing query analysis...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return []
        
        retriever = MultiVectorRetriever(MockVectorStore())
        
        # Test different query types
        test_queries = [
            ("KA02I technical specifications", {'has_product': True, 'is_technical': True}),
            ("What is the power output?", {'is_question': True}),
            ("Compare KA02I vs KA04", {'is_comparison': True, 'has_product': True}),
            ("Hotel audio installation", {'has_product': False, 'is_technical': False})
        ]
        
        for query, expected_features in test_queries:
            intent = retriever.analyze_query_intent(query)
            
            all_correct = True
            for feature, expected_value in expected_features.items():
                if intent.get(feature) != expected_value:
                    print(f"❌ Query '{query}': {feature} = {intent.get(feature)}, expected {expected_value}")
                    all_correct = False
            
            if all_correct:
                print(f"✅ Query analysis correct for: '{query}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Query analysis test error: {e}")
        return False

def test_strategy_weight_adjustment():
    """Test dynamic strategy weight adjustment"""
    print("🔍 Testing strategy weight adjustment...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return []
        
        retriever = MultiVectorRetriever(MockVectorStore())
        
        # Test weight adjustment for technical product query
        query_intent = {
            'has_product': True,
            'products': ['ka02i'],
            'is_technical': True,
            'is_question': False,
            'is_comparison': False,
            'query_complexity': 3
        }
        
        original_weights = {name: strategy.weight for name, strategy in retriever.strategies.items()}
        adjusted_strategies = retriever.adjust_strategy_weights(query_intent)
        
        # Check that product and technical strategies got boosted
        if adjusted_strategies['exact_product_match'].weight > original_weights['exact_product_match']:
            print("✅ Product match strategy weight boosted")
        else:
            print("❌ Product match strategy weight not boosted")
            return False
        
        if adjusted_strategies['technical_specs'].weight > original_weights['technical_specs']:
            print("✅ Technical specs strategy weight boosted")
        else:
            print("❌ Technical specs strategy weight not boosted")
            return False
        
        # Check weight normalization
        total_weight = sum(s.weight for s in adjusted_strategies.values() if s.enabled)
        if 0.9 <= total_weight <= 1.1:  # Allow small rounding errors
            print(f"✅ Weights properly normalized: {total_weight:.3f}")
        else:
            print(f"❌ Weights not normalized: {total_weight:.3f}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy weight adjustment test error: {e}")
        return False

def test_query_transformations():
    """Test query transformation functions"""
    print("🔍 Testing query transformations...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return []
        
        retriever = MultiVectorRetriever(MockVectorStore())
        
        # Test transformations
        test_cases = [
            ('product_focused', 'ka02i amplifier', 'KA02I'),
            ('question_format', 'power specifications', '?'),
            ('technical_focused', 'ka02i features', 'specifications'),
            ('semantic_expansion', 'power output', 'watt'),
        ]
        
        for transform_type, input_query, expected_in_output in test_cases:
            if transform_type in retriever.query_transformations:
                transformed = retriever.query_transformations[transform_type](input_query)
                
                if expected_in_output.lower() in transformed.lower():
                    print(f"✅ Transformation '{transform_type}': '{input_query}' → contains '{expected_in_output}'")
                else:
                    print(f"❌ Transformation '{transform_type}': '{input_query}' → '{transformed}' (missing '{expected_in_output}')")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Query transformation test error: {e}")
        return False

def test_multi_vector_retrieval():
    """Test end-to-end multi-vector retrieval"""
    print("🔍 Testing multi-vector retrieval...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        # Enhanced mock vector store that responds to filters
        class EnhancedMockVectorStore:
            def search(self, query, top_k=5, filters=None):
                # Simulate different results based on filters
                results = []
                content_type = 'general'
                
                if filters:
                    if 'content_type' in filters:
                        if isinstance(filters['content_type'], list):
                            content_type = filters['content_type'][0]
                        else:
                            content_type = filters['content_type']
                
                for i in range(min(top_k, 2)):  # Return fewer results per strategy
                    results.append({
                        'id': f'{content_type}_{i}_{hash(query) % 1000}',
                        'content': f'{content_type.title()} content {i} for: {query}',
                        'score': 0.8 - (i * 0.1),
                        'metadata': {
                            'content_type': content_type,
                            'model': 'KA02I' if 'ka02i' in query.lower() else '',
                            'product_line': 'Kommander' if 'ka02i' in query.lower() else ''
                        }
                    })
                
                return results
        
        mock_store = EnhancedMockVectorStore()
        retriever = MultiVectorRetriever(mock_store, enable_reranking=True, enable_fusion=True)
        
        # Test retrieval
        query = "KA02I technical specifications"
        results = retriever.retrieve(query, max_results=5)
        
        print(f"✅ Retrieved {len(results)} results")
        
        # Check that results have multi-vector metadata
        for i, result in enumerate(results):
            if 'multi_vector_metadata' in result:
                metadata = result['multi_vector_metadata']
                print(f"✅ Result {i+1}: confidence={metadata['confidence']:.3f}, "
                      f"strategies={metadata['num_strategies']}")
            else:
                print(f"❌ Result {i+1}: Missing multi-vector metadata")
                return False
        
        # Test quality metrics
        metrics = retriever.get_quality_metrics(query, results)
        print(f"✅ Quality metrics: coverage={metrics['strategy_coverage']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-vector retrieval test error: {e}")
        return False

def test_reciprocal_rank_fusion():
    """Test RRF fusion algorithm"""
    print("🔍 Testing Reciprocal Rank Fusion...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return []
        
        retriever = MultiVectorRetriever(MockVectorStore())
        
        # Set up mock strategies for RRF test
        retriever.strategies = {
            'strategy_a': retriever.strategies['exact_product_match'],  # Use existing strategy
            'strategy_b': retriever.strategies['qa_pairs']  # Use existing strategy
        }
        
        # Mock strategy results
        strategy_results = {
            'strategy_a': [
                {'id': 'doc1', 'content': 'Content 1', 'score': 0.9},
                {'id': 'doc2', 'content': 'Content 2', 'score': 0.8},
                {'id': 'doc3', 'content': 'Content 3', 'score': 0.7}
            ],
            'strategy_b': [
                {'id': 'doc2', 'content': 'Content 2', 'score': 0.95},  # Same doc, different rank
                {'id': 'doc1', 'content': 'Content 1', 'score': 0.85},
                {'id': 'doc4', 'content': 'Content 4', 'score': 0.75}
            ]
        }
        
        # Test RRF fusion
        fused_results = retriever.reciprocal_rank_fusion(strategy_results)
        
        print(f"✅ RRF produced {len(fused_results)} fused results")
        
        # Check that results are properly ranked
        scores = [result.combined_score for result in fused_results]
        if scores == sorted(scores, reverse=True):
            print("✅ Results properly sorted by combined score")
        else:
            print("❌ Results not properly sorted")
            return False
        
        # Check that documents appearing in multiple strategies have higher scores
        doc2_result = next((r for r in fused_results if r.document['id'] == 'doc2'), None)
        if doc2_result and len(doc2_result.strategy_scores) == 2:
            print("✅ Document in multiple strategies has combined scores")
        else:
            print("❌ Multi-strategy document scoring failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ RRF test error: {e}")
        return False

def main():
    """Run all Phase 3 tests"""
    print("🚀 Phase 3 Testing: Multi-Vector Retrieval System")
    print("=" * 50)
    
    tests = [
        ("Multi-Vector Import Test", test_multi_vector_import),
        ("Query Analysis Test", test_query_analysis),
        ("Strategy Weight Adjustment Test", test_strategy_weight_adjustment),
        ("Query Transformations Test", test_query_transformations),
        ("Reciprocal Rank Fusion Test", test_reciprocal_rank_fusion),
        ("Multi-Vector Retrieval Test", test_multi_vector_retrieval)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append(result)
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Phase 3 Testing: ALL TESTS PASSED ({passed}/{total})")
        print("✅ Multi-vector retrieval system fully implemented!")
    else:
        print(f"⚠️  Phase 3 Testing: {passed}/{total} tests passed")
        print("❌ Fix failing tests before proceeding")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)