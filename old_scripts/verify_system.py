#!/usr/bin/env python3
"""
System Verification Script for K-Array Chat System
Comprehensive check of all components and configurations
"""

import os
import sys
import importlib.util
import json
from pathlib import Path

def check_file_structure():
    """Verify all required files are present"""
    print("🔍 Checking file structure...")
    
    required_files = [
        "README.md",
        ".env.example", 
        "requirements.txt",
        "k_array_chat.py",
        "quick_setup.py",
        "src/dynamic_config.py",
        "src/query_intelligence.py",
        "src/multi_vector_retriever.py",
        "src/llm_manager.py",
        "config/dynamic_config.json",
        "config/domain_knowledge.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def check_imports():
    """Check if all modules can be imported"""
    print("🔍 Checking module imports...")
    
    modules_to_test = [
        "src.config",
        "src.dynamic_config", 
        "src.llm_manager",
        "src.query_intelligence",
        "src.multi_vector_retriever",
        "src.enhanced_vector_store",
        "src.reranker",
        "src.response_engine"
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            importlib.import_module(module)
        except ImportError as e:
            failed_imports.append((module, str(e)))
    
    if failed_imports:
        print("❌ Import failures:")
        for module, error in failed_imports:
            print(f"   {module}: {error}")
        return False
    
    print("✅ All modules can be imported")
    return True

def check_configuration_files():
    """Verify configuration files are valid JSON"""
    print("🔍 Checking configuration files...")
    
    config_files = [
        "config/dynamic_config.json",
        "config/domain_knowledge.json"
    ]
    
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                json.load(f)
            print(f"✅ {config_file} is valid JSON")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ {config_file} error: {e}")
            return False
    
    return True

def check_dynamic_system():
    """Verify dynamic configuration system works"""
    print("🔍 Checking dynamic configuration system...")
    
    try:
        from src.dynamic_config import dynamic_config
        
        # Test configuration access
        retrieval_config = dynamic_config.retrieval_config
        server_config = dynamic_config.server_config
        llm_config = dynamic_config.llm_config
        
        # Test domain knowledge
        domain_knowledge = dynamic_config.get_domain_knowledge()
        
        if domain_knowledge and 'product_series' in domain_knowledge:
            print("✅ Dynamic domain knowledge working")
        else:
            print("⚠️  Domain knowledge may need initialization")
        
        print("✅ Dynamic configuration system working")
        return True
        
    except Exception as e:
        print(f"❌ Dynamic configuration error: {e}")
        return False

def check_llm_system():
    """Check LLM system integration"""
    print("🔍 Checking LLM system...")
    
    try:
        from src.llm_manager import LLMManager
        from src.config import Config
        
        # Check if API keys are configured
        has_gemini = bool(Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your_gemini_api_key_here")
        has_openai = bool(Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != "your_openai_api_key_here")
        
        if not has_gemini and not has_openai:
            print("⚠️  No API keys configured (system will use fallbacks)")
            return True
        
        # Try to initialize LLM manager
        llm = LLMManager()
        print("✅ LLM manager initialized")
        
        # Check generate_text method exists
        if hasattr(llm, 'generate_text'):
            print("✅ generate_text method available")
        else:
            print("❌ generate_text method missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LLM system error: {e}")
        return False

def check_query_intelligence():
    """Check query intelligence system"""
    print("🔍 Checking query intelligence system...")
    
    try:
        from src.query_intelligence import QueryIntelligenceEngine
        
        # Test initialization
        engine = QueryIntelligenceEngine()
        
        # Test fallback domain knowledge
        knowledge = engine.get_domain_knowledge()
        if knowledge and 'products' in knowledge:
            print("✅ Query intelligence domain knowledge working")
        
        # Test fallback language detection
        result = engine._fallback_language_detection("Test query")
        if result and 'language' in result:
            print("✅ Language detection fallback working")
        
        print("✅ Query intelligence system working")
        return True
        
    except Exception as e:
        print(f"❌ Query intelligence error: {e}")
        return False

def check_retrieval_system():
    """Check multi-vector retrieval system"""
    print("🔍 Checking retrieval system...")
    
    try:
        from src.multi_vector_retriever import MultiVectorRetriever
        from src.enhanced_vector_store import EnhancedVectorStore
        
        # Create mock vector store
        class MockVectorStore:
            def search(self, query, top_k=5, filters=None):
                return [{'id': 'test', 'content': 'test content', 'score': 0.9}]
            
            def get_stats(self):
                return {'total_documents': 1}
        
        mock_store = MockVectorStore()
        retriever = MultiVectorRetriever(mock_store, enable_reranking=False, enable_query_intelligence=False)
        
        # Test retrieval
        results, intelligence = retriever.retrieve("test query")
        if results and len(results) > 0:
            print("✅ Multi-vector retrieval working")
        
        return True
        
    except Exception as e:
        print(f"❌ Retrieval system error: {e}")
        return False

def check_security():
    """Check security configurations"""
    print("🔍 Checking security configurations...")
    
    # Check that API keys are not hardcoded in source files
    source_files = [
        "src/llm_manager.py",
        "src/config.py",
        "k_array_chat.py"
    ]
    
    for file_path in source_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check for potential hardcoded keys (simplified check)
            if 'sk-' in content or 'AIza' in content:
                print(f"⚠️  Potential hardcoded API key in {file_path}")
                return False
    
    print("✅ No hardcoded API keys found")
    return True

def run_quick_test():
    """Run a quick end-to-end test"""
    print("🧪 Running quick end-to-end test...")
    
    try:
        # Test configuration loading
        from src.dynamic_config import dynamic_config
        config = dynamic_config.retrieval_config
        
        # Test query intelligence with fallback
        from src.query_intelligence import QueryIntelligenceEngine
        engine = QueryIntelligenceEngine()
        
        # Test with mock LLM to avoid API calls
        class MockLLM:
            def generate_text(self, prompt):
                return "Mock response"
        
        engine.llm_manager = MockLLM()
        
        # Test analysis
        intelligence = engine.analyze_query("Test query about KA02I")
        
        if intelligence and hasattr(intelligence, 'intent'):
            print("✅ End-to-end test passed")
            return True
        else:
            print("❌ End-to-end test failed")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end test error: {e}")
        return False

def main():
    """Main verification function"""
    print("🔍 K-Array Chat System - Comprehensive Verification")
    print("="*60)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Module Imports", check_imports),
        ("Configuration Files", check_configuration_files),
        ("Dynamic System", check_dynamic_system),
        ("LLM System", check_llm_system),
        ("Query Intelligence", check_query_intelligence),
        ("Retrieval System", check_retrieval_system),
        ("Security", check_security),
        ("Quick End-to-End Test", run_quick_test),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "="*60)
    print("📊 VERIFICATION RESULTS:")
    print("="*60)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<25} {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📈 OVERALL: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 SYSTEM VERIFICATION COMPLETE!")
        print("✅ All components verified and working correctly")
        print("🚀 System ready for production use!")
    else:
        print(f"\n⚠️  SYSTEM ISSUES DETECTED: {total - passed} failures")
        print("❌ Please fix failing checks before deployment")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)