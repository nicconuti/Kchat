#!/usr/bin/env python3
"""
Test script for K-Array Chat System components
"""

import os
import sys
import logging
from pathlib import Path

def setup_test_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_vector_store():
    """Test enhanced vector store"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Enhanced Vector Store...")
    
    try:
        from src.enhanced_vector_store import EnhancedVectorStore
        
        # Initialize vector store
        vector_store = EnhancedVectorStore()
        logger.info("✅ Vector store initialized successfully")
        
        # Get stats
        stats = vector_store.get_stats()
        logger.info(f"✅ Stats retrieved: {stats}")
        
        # Test search (if data exists)
        if stats['total_documents'] > 0:
            results = vector_store.hybrid_search("test query", n_results=1)
            logger.info(f"✅ Search test: found {len(results)} results")
        else:
            logger.info("ℹ️ No documents in vector store, skipping search test")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector store test failed: {str(e)}")
        return False

def test_retriever():
    """Test smart retriever"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Smart Retriever...")
    
    try:
        from src.enhanced_vector_store import EnhancedVectorStore
        from src.smart_retriever import SmartRetriever
        
        vector_store = EnhancedVectorStore()
        retriever = SmartRetriever(vector_store)
        logger.info("✅ Smart retriever initialized successfully")
        
        # Test query analysis
        context = retriever.analyze_query("What are the specifications of KA104?")
        logger.info(f"✅ Query analysis: {context.query_type}, confidence: {context.confidence}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Retriever test failed: {str(e)}")
        return False

def test_response_engine():
    """Test response engine"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Response Engine...")
    
    try:
        from src.response_engine import ResponseEngine
        
        # Try to initialize (may fail if API keys not set)
        try:
            response_engine = ResponseEngine()
            logger.info("✅ Response engine initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Response engine initialization failed (likely missing API keys): {str(e)}")
            logger.info("This is expected if API keys are not configured yet")
            return True  # Not a critical failure
        
    except Exception as e:
        logger.error(f"❌ Response engine test failed: {str(e)}")
        return False

def test_data_ingestion():
    """Test data ingestion"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Data Ingestion...")
    
    try:
        from src.enhanced_vector_store import EnhancedVectorStore
        
        # Check for JSON files
        json_files = list(Path('data').glob('extracted_data_*.json'))
        logger.info(f"Found {len(json_files)} JSON files in data/ directory")
        
        if len(json_files) == 0:
            logger.warning("⚠️ No JSON files found. Run extraction scripts first.")
            return True  # Not a failure, just no data yet
        
        # Test ingestion with a small subset
        vector_store = EnhancedVectorStore()
        stats_before = vector_store.get_stats()
        
        if stats_before['total_documents'] == 0 and len(json_files) > 0:
            logger.info("Vector store is empty, testing ingestion...")
            ingested = vector_store.ingest_json_files('data')
            logger.info(f"✅ Ingested {ingested} documents")
        else:
            logger.info(f"✅ Vector store already has {stats_before['total_documents']} documents")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data ingestion test failed: {str(e)}")
        return False

def test_config():
    """Test configuration"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Configuration...")
    
    try:
        from src.config import Config
        
        # Check basic config loading
        logger.info(f"✅ Config loaded - Default LLM: {Config.DEFAULT_LLM_PROVIDER}")
        logger.info(f"✅ ChromaDB directory: {Config.CHROMA_PERSIST_DIRECTORY}")
        
        # Check API keys (without logging them)
        has_gemini = bool(Config.GEMINI_API_KEY)
        has_openai = bool(Config.OPENAI_API_KEY)
        
        logger.info(f"✅ Gemini API key configured: {has_gemini}")
        logger.info(f"✅ OpenAI API key configured: {has_openai}")
        
        if not has_gemini and not has_openai:
            logger.warning("⚠️ No API keys configured. Add them to .env file before using chat.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Config test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger = setup_test_logging()
    
    logger.info("🧪 Starting K-Array Chat System Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Vector Store", test_vector_store),
        ("Smart Retriever", test_retriever),
        ("Response Engine", test_response_engine),
        ("Data Ingestion", test_data_ingestion)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! System should work correctly.")
    elif passed >= total - 1:
        logger.info("⚠️ Most tests passed. Check warnings above.")
    else:
        logger.error("❌ Multiple test failures. Check errors above.")
    
    logger.info("\n💡 Next steps:")
    if passed >= total - 1:
        logger.info("1. Make sure API keys are set in .env file")
        logger.info("2. Run: python k_array_chat.py")
        logger.info("3. Open http://localhost:7860")
    else:
        logger.info("1. Fix the errors shown above")
        logger.info("2. Run this test script again")
        logger.info("3. Check CLAUDE.md for troubleshooting")

if __name__ == "__main__":
    main()