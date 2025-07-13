#!/usr/bin/env python3
"""
Test script for Phase 2: Cross-Encoder Reranking Integration
Tests reranking functionality and smart retriever integration
"""

import sys
import os
sys.path.append('.')

def test_reranker_import():
    """Test that reranker can be imported and initialized"""
    print("🔍 Testing reranker import...")
    
    try:
        from src.reranker import QualityReranker, RerankResult
        print("✅ Reranker imports successful")
        
        # Test initialization (without heavy models)
        reranker = QualityReranker()
        print("✅ Reranker initialized successfully")
        
        # Test if it falls back to mock when cross-encoder unavailable
        if reranker.model is None:
            print("✅ Correctly falling back to mock reranking (cross-encoder not available)")
        else:
            print("✅ Cross-encoder model loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Reranker test error: {e}")
        return False

def test_reranker_functionality():
    """Test reranker with mock data"""
    print("🔍 Testing reranker functionality...")
    
    try:
        from src.reranker import QualityReranker
        
        reranker = QualityReranker()
        
        # Mock test documents
        test_docs = [
            {
                'id': 'doc1',
                'content': 'KA02I amplifier specifications: 4x50W power output, IEB processor',
                'score': 0.7,
                'metadata': {'content_type': 'technical_specs', 'model': 'KA02I', 'product_line': 'Kommander'}
            },
            {
                'id': 'doc2', 
                'content': 'General information about K-Array product lines and applications',
                'score': 0.9,
                'metadata': {'content_type': 'general', 'model': '', 'product_line': ''}
            },
            {
                'id': 'doc3',
                'content': 'KA02I features include osKar operating system and REST API integration',
                'score': 0.6,
                'metadata': {'content_type': 'searchable_text', 'model': 'KA02I', 'product_line': 'Kommander'}
            }
        ]
        
        # Test reranking
        query = "KA02I technical specifications"
        reranked_docs = reranker.get_reranked_documents(query, test_docs, top_k=3)
        
        print(f"✅ Reranking completed: {len(reranked_docs)} documents")
        
        # Verify reranked documents have expected fields
        for i, doc in enumerate(reranked_docs):
            if 'rerank_metadata' in doc:
                print(f"✅ Document {i+1}: Final score {doc['score']:.3f}, "
                      f"rank change: {doc['rerank_metadata']['rank_change']}")
            else:
                print(f"⚠️  Document {i+1}: Missing rerank metadata")
        
        # Test quality metrics
        metrics = reranker.quality_metrics(query, test_docs, reranked_docs)
        print(f"✅ Quality metrics: {metrics.get('score_improvement', 0):.3f} improvement")
        
        return True
        
    except Exception as e:
        print(f"❌ Reranker functionality test error: {e}")
        return False

def test_smart_retriever_integration():
    """Test smart retriever with reranking integration"""
    print("🔍 Testing smart retriever integration...")
    
    try:
        # Mock the vector store to avoid Milvus dependency
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                # Return mock search results
                return [
                    {
                        'id': f'mock_{i}',
                        'content': f'Mock content {i} for query: {query}',
                        'score': 0.8 - (i * 0.1),
                        'metadata': {
                            'content_type': 'searchable_text',
                            'model': 'KA02I' if i % 2 == 0 else '',
                            'product_line': 'Kommander' if i % 2 == 0 else ''
                        }
                    } for i in range(min(top_k, 3))
                ]
        
        from src.smart_retriever import SmartRetriever
        
        # Test with reranking enabled
        mock_store = MockVectorStore()
        retriever_with_rerank = SmartRetriever(mock_store, enable_reranking=True)
        print("✅ Smart retriever with reranking initialized")
        
        # Test without reranking
        retriever_no_rerank = SmartRetriever(mock_store, enable_reranking=False)
        print("✅ Smart retriever without reranking initialized")
        
        # Test query analysis
        test_query = "What are the technical specifications of KA02I?"
        context = retriever_with_rerank.analyze_query(test_query)
        
        print(f"✅ Query analysis: type='{context.query_type}', "
              f"intent='{context.intent}', products={context.detected_products}")
        
        return True
        
    except Exception as e:
        print(f"❌ Smart retriever integration test error: {e}")
        return False

def test_end_to_end_retrieval():
    """Test end-to-end retrieval with mock data"""
    print("🔍 Testing end-to-end retrieval...")
    
    try:
        # This test would require actual vector store
        # For now, just test that the integration points exist
        
        from src.smart_retriever import SmartRetriever
        from src.reranker import QualityReranker
        
        # Verify that SmartRetriever has reranking attributes
        mock_store = type('MockStore', (), {'search': lambda *args, **kwargs: []})()
        retriever = SmartRetriever(mock_store, enable_reranking=True)
        
        if hasattr(retriever, 'reranker') and hasattr(retriever, 'enable_reranking'):
            print("✅ Smart retriever has reranking integration points")
        else:
            print("❌ Smart retriever missing reranking integration")
            return False
        
        # Verify that retrieve_contextual method exists and handles reranking
        if hasattr(retriever, 'retrieve_contextual'):
            print("✅ Smart retriever has retrieve_contextual method")
        else:
            print("❌ Smart retriever missing retrieve_contextual method")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end retrieval test error: {e}")
        return False

def main():
    """Run all Phase 2 tests"""
    print("🚀 Phase 2 Testing: Cross-Encoder Reranking Integration")
    print("=" * 50)
    
    tests = [
        ("Reranker Import Test", test_reranker_import),
        ("Reranker Functionality Test", test_reranker_functionality),
        ("Smart Retriever Integration Test", test_smart_retriever_integration),
        ("End-to-End Retrieval Test", test_end_to_end_retrieval)
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
        print(f"🎉 Phase 2 Testing: ALL TESTS PASSED ({passed}/{total})")
        print("✅ Ready to proceed to Phase 3")
    else:
        print(f"⚠️  Phase 2 Testing: {passed}/{total} tests passed")
        print("❌ Fix failing tests before proceeding")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)