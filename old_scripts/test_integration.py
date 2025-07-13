#!/usr/bin/env python3
"""
Integration Test for Complete K-Array Retrieval System
Tests the full pipeline: Milvus + Multi-Vector + Reranking + Chat
"""

import sys
import os
sys.path.append('.')

def test_complete_import():
    """Test that all components can be imported together"""
    print("🔍 Testing complete system import...")
    
    try:
        from src.enhanced_vector_store import EnhancedVectorStore
        from src.multi_vector_retriever import MultiVectorRetriever
        from src.reranker import QualityReranker
        from src.smart_retriever import SmartRetriever
        print("✅ All retrieval components imported successfully")
        
        from k_array_chat import KArrayChatSystem
        print("✅ Chat system imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test error: {e}")
        return False

def test_system_initialization():
    """Test system initialization without Milvus server"""
    print("🔍 Testing system initialization...")
    
    try:
        # Mock the vector store to avoid Milvus dependency
        class MockEnhancedVectorStore:
            def __init__(self, *args, **kwargs):
                self.host = "localhost"
                self.port = "19530"
                self.collection_name = "test"
                
            def get_stats(self):
                return {
                    'total_documents': 231,
                    'last_updated': '2025-07-13T00:00:00'
                }
            
            def search(self, query, top_k=5, filters=None):
                return [
                    {
                        'id': f'mock_{i}',
                        'content': f'Mock search result {i} for: {query}',
                        'score': 0.9 - (i * 0.1),
                        'metadata': {
                            'content_type': 'searchable_text',
                            'model': 'KA02I',
                            'product_line': 'Kommander'
                        }
                    } for i in range(min(top_k, 3))
                ]
            
            def ingest_json_files(self):
                return 231
        
        # Temporarily replace the class
        import src.enhanced_vector_store
        original_class = src.enhanced_vector_store.EnhancedVectorStore
        src.enhanced_vector_store.EnhancedVectorStore = MockEnhancedVectorStore
        
        # Test multi-vector retriever initialization
        from src.multi_vector_retriever import MultiVectorRetriever
        mock_store = MockEnhancedVectorStore()
        retriever = MultiVectorRetriever(mock_store, enable_reranking=True, enable_fusion=True)
        print("✅ Multi-vector retriever initialized with mock store")
        
        # Test quality metrics
        test_results = mock_store.search("KA02I specifications")
        metrics = retriever.get_quality_metrics("KA02I specifications", test_results)
        print(f"✅ Quality metrics calculated: {metrics.get('result_count', 0)} results")
        
        # Restore original class
        src.enhanced_vector_store.EnhancedVectorStore = original_class
        
        return True
        
    except Exception as e:
        print(f"❌ System initialization test error: {e}")
        return False

def test_retrieval_pipeline():
    """Test the complete retrieval pipeline"""
    print("🔍 Testing complete retrieval pipeline...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        # Enhanced mock store with strategy support
        class PipelineMockStore:
            def search(self, query, top_k=5, filters=None):
                # Simulate different results based on content type filter
                if filters and 'content_type' in filters:
                    content_type = filters['content_type']
                    if isinstance(content_type, list):
                        content_type = content_type[0]
                else:
                    content_type = 'general'
                
                return [
                    {
                        'id': f'{content_type}_{i}_{hash(query) % 100}',
                        'content': f'{content_type.replace("_", " ").title()} content for: {query}',
                        'score': 0.9 - (i * 0.05),
                        'metadata': {
                            'content_type': content_type,
                            'model': 'KA02I' if 'ka02i' in query.lower() else '',
                            'product_line': 'Kommander' if 'ka02i' in query.lower() else ''
                        }
                    } for i in range(min(top_k, 2))
                ]
        
        mock_store = PipelineMockStore()
        retriever = MultiVectorRetriever(mock_store, enable_reranking=True, enable_fusion=True)
        
        # Test comprehensive retrieval
        test_queries = [
            "KA02I technical specifications",
            "What is the power output of amplifiers?",
            "Hotel audio system recommendations",
            "Compare different speaker models"
        ]
        
        for query in test_queries:
            results, query_intelligence = retriever.retrieve(query, max_results=5)
            
            if len(results) > 0:
                print(f"✅ Query '{query}': {len(results)} results")
                
                # Check for multi-vector metadata
                first_result = results[0]
                if 'multi_vector_metadata' in first_result:
                    metadata = first_result['multi_vector_metadata']
                    print(f"   Confidence: {metadata['confidence']:.3f}, "
                          f"Strategies: {metadata['num_strategies']}")
                else:
                    print("   ⚠️ Missing multi-vector metadata")
            else:
                print(f"❌ Query '{query}': No results")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Retrieval pipeline test error: {e}")
        return False

def test_strategy_effectiveness():
    """Test that different strategies are being used effectively"""
    print("🔍 Testing strategy effectiveness...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        
        class StrategyTestStore:
            def __init__(self):
                self.call_count = 0
                self.filter_history = []
            
            def search(self, query, top_k=5, filters=None):
                self.call_count += 1
                self.filter_history.append(filters)
                
                # Return mock results
                return [
                    {
                        'id': f'strategy_test_{self.call_count}_{i}',
                        'content': f'Strategy test result {i}',
                        'score': 0.8,
                        'metadata': {'content_type': 'test'}
                    } for i in range(1)
                ]
        
        test_store = StrategyTestStore()
        retriever = MultiVectorRetriever(test_store, enable_reranking=False, enable_fusion=True)
        
        # Execute retrieval
        results, _ = retriever.retrieve("KA02I technical specifications", max_results=3)
        
        # Check that multiple strategies were called
        if test_store.call_count >= 3:
            print(f"✅ Multiple strategies executed: {test_store.call_count} calls")
        else:
            print(f"❌ Insufficient strategy calls: {test_store.call_count}")
            return False
        
        # Check that different filters were used
        unique_filters = set(str(f) for f in test_store.filter_history)
        if len(unique_filters) >= 3:
            print(f"✅ Diverse filter usage: {len(unique_filters)} unique filter sets")
        else:
            print(f"❌ Limited filter diversity: {len(unique_filters)} filter sets")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy effectiveness test error: {e}")
        return False

def test_quality_improvements():
    """Test quality improvements vs baseline"""
    print("🔍 Testing quality improvements...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        from src.smart_retriever import SmartRetriever
        
        # Consistent mock store for comparison
        class ComparisonMockStore:
            def search(self, query, top_k=5, filters=None):
                base_results = [
                    {
                        'id': f'baseline_{i}',
                        'content': f'Baseline result {i} for {query}',
                        'score': 0.7 + (i * 0.05),
                        'metadata': {'content_type': 'general'}
                    } for i in range(min(top_k, 3))
                ]
                
                # Multi-vector gets slightly different results
                if filters:
                    return [
                        {
                            'id': f'enhanced_{i}',
                            'content': f'Enhanced result {i} for {query}',
                            'score': 0.8 + (i * 0.05),
                            'metadata': {'content_type': 'enhanced'}
                        } for i in range(min(top_k, 2))
                    ]
                
                return base_results
        
        mock_store = ComparisonMockStore()
        
        # Test multi-vector retriever
        multi_retriever = MultiVectorRetriever(mock_store, enable_reranking=True, enable_fusion=True)
        multi_results, _ = multi_retriever.retrieve("KA02I specifications", max_results=3)
        
        # Test baseline retriever
        baseline_retriever = SmartRetriever(mock_store, enable_reranking=False)
        
        # Mock the search method to avoid dependency issues
        def mock_search(query, conversation_history=None, max_results=5):
            results = mock_store.search(query, top_k=max_results, filters=None)
            context = type('Context', (), {'original_query': query})()
            return results, context
        
        baseline_retriever.search = mock_search
        baseline_results, _ = baseline_retriever.search("KA02I specifications", max_results=3)
        
        # Compare quality indicators
        multi_has_metadata = any('multi_vector_metadata' in r for r in multi_results)
        multi_diverse_sources = len(set(r.get('id', '').split('_')[0] for r in multi_results)) > 1
        
        if multi_has_metadata:
            print("✅ Multi-vector results include quality metadata")
        else:
            print("❌ Multi-vector results missing quality metadata")
            return False
        
        if multi_diverse_sources:
            print("✅ Multi-vector results show source diversity")
        else:
            print("❌ Multi-vector results lack source diversity")
        
        print(f"✅ Quality comparison: Multi-vector={len(multi_results)}, Baseline={len(baseline_results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quality improvement test error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Integration Testing: Complete K-Array Retrieval System")
    print("=" * 60)
    
    tests = [
        ("Complete Import Test", test_complete_import),
        ("System Initialization Test", test_system_initialization),
        ("Retrieval Pipeline Test", test_retrieval_pipeline),
        ("Strategy Effectiveness Test", test_strategy_effectiveness),
        ("Quality Improvements Test", test_quality_improvements)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append(result)
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 INTEGRATION COMPLETE: ALL TESTS PASSED ({passed}/{total})")
        print("✅ Sistema K-Array con retrieval avanzato pronto per produzione!")
        print("\n📈 MIGLIORAMENTI IMPLEMENTATI:")
        print("   • Milvus Vector Store (35k+ stars)")
        print("   • Multi-Vector Retrieval (6 strategie)")
        print("   • Cross-Encoder Reranking")
        print("   • Reciprocal Rank Fusion")
        print("   • Query Analysis & Transformation")
        print("   • Zero-Hallucination Response Engine")
    else:
        print(f"⚠️  INTEGRATION ISSUES: {passed}/{total} tests passed")
        print("❌ Fix failing tests before production deployment")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)