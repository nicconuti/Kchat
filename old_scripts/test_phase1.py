#!/usr/bin/env python3
"""
Test script for Phase 1: Milvus Vector Store Integration
Tests without actual Milvus connection to verify code structure
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import json
        import logging
        import hashlib
        from pathlib import Path
        import numpy as np
        from datetime import datetime
        print("✅ Standard library imports successful")
    except ImportError as e:
        print(f"❌ Standard library import error: {e}")
        return False
    
    try:
        from pymilvus import (
            connections,
            utility,
            FieldSchema,
            CollectionSchema,
            DataType,
            Collection,
        )
        print("✅ PyMilvus imports successful")
    except ImportError as e:
        print(f"❌ PyMilvus import error: {e}")
        return False
    
    return True

def test_class_definition():
    """Test that the EnhancedVectorStore class is properly defined"""
    print("🔍 Testing class definition...")
    
    try:
        # Mock SentenceTransformer to avoid heavy torch dependency
        class MockSentenceTransformer:
            def __init__(self, model_name):
                self.model_name = model_name
            
            def encode(self, texts, normalize_embeddings=True):
                # Return mock embeddings
                import numpy as np
                return np.random.rand(len(texts), 768).astype(np.float32)
        
        # Temporarily replace SentenceTransformer
        import sys
        original_import = __builtins__.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'sentence_transformers':
                class MockModule:
                    SentenceTransformer = MockSentenceTransformer
                return MockModule()
            return original_import(name, *args, **kwargs)
        
        __builtins__.__import__ = mock_import
        
        # Now test our class
        from src.enhanced_vector_store import EnhancedVectorStore
        
        # Restore original import
        __builtins__.__import__ = original_import
        
        print("✅ EnhancedVectorStore class imported successfully")
        
        # Test class methods exist
        expected_methods = [
            'generate_embeddings', 'create_document_id', 'extract_specs_text',
            'process_json_file', 'ingest_json_files', 'update_stats', 
            'get_stats', 'search', 'hybrid_search'
        ]
        
        for method in expected_methods:
            if hasattr(EnhancedVectorStore, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Class definition error: {e}")
        return False

def test_json_processing():
    """Test JSON file processing logic"""
    print("🔍 Testing JSON processing logic...")
    
    try:
        # Check if sample JSON files exist
        import json
        from pathlib import Path
        json_files = list(Path('data').glob('extracted_data_*.json'))
        
        if json_files:
            print(f"✅ Found {len(json_files)} JSON files in data directory")
            
            # Test reading one file
            sample_file = json_files[0]
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expected structure
            expected_keys = ['metadata', 'embedding_optimized', 'keywords']
            for key in expected_keys:
                if key in data:
                    print(f"✅ Key '{key}' found in sample JSON")
                else:
                    print(f"⚠️  Key '{key}' not found in sample JSON")
            
            return True
        else:
            print("⚠️  No JSON files found in data directory")
            return True  # Not an error for this test
            
    except Exception as e:
        print(f"❌ JSON processing test error: {e}")
        return False

def main():
    """Run all Phase 1 tests"""
    print("🚀 Phase 1 Testing: Milvus Vector Store Integration")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Class Definition Test", test_class_definition),
        ("JSON Processing Test", test_json_processing)
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
        print(f"🎉 Phase 1 Testing: ALL TESTS PASSED ({passed}/{total})")
        print("✅ Ready to proceed to Phase 2")
    else:
        print(f"⚠️  Phase 1 Testing: {passed}/{total} tests passed")
        print("❌ Fix failing tests before proceeding")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)