#!/usr/bin/env python3
"""
Setup script for K-Array Chat System
Initializes vector store and processes JSON data
"""

import os
import logging
from pathlib import Path
from src.enhanced_vector_store import EnhancedVectorStore
from src.config import Config

def setup_logging():
    """Setup logging for setup script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_environment():
    """Check if environment is properly configured"""
    logger = logging.getLogger(__name__)
    
    logger.info("Checking environment configuration...")
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        logger.warning(".env file not found. Creating template...")
        with open('.env', 'w') as f:
            f.write("""# K-Array Chat System Configuration
# Add your API keys here

# Gemini AI (primary LLM)
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI (fallback LLM)
OPENAI_API_KEY=your_openai_api_key_here

# Default LLM provider
DEFAULT_LLM_PROVIDER=gemini

# Vector Store settings
VECTOR_STORE_DIRECTORY=./data/vector_store
""")
        logger.info("Created .env template. Please add your API keys before running the chat system.")
        return False
    
    # Check API keys
    try:
        Config.validate_config()
        logger.info("✅ Environment configuration is valid")
        return True
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.info("Please check your .env file and add the required API keys.")
        return False

def setup_directories():
    """Create necessary directories"""
    logger = logging.getLogger(__name__)
    
    directories = [
        'data',
        'data/vector_store',
        'data/extraction_logs',
        'data/quality_reports',
        'uploads'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directory created/verified: {directory}")

def initialize_vector_store():
    """Initialize and populate vector store"""
    logger = logging.getLogger(__name__)
    
    logger.info("Initializing vector store...")
    
    try:
        # Initialize vector store
        vector_store = EnhancedVectorStore()
        
        # Check if already populated
        stats = vector_store.get_stats()
        if stats['total_documents'] > 0:
            logger.info(f"Vector store already contains {stats['total_documents']} documents")
            return True
        
        # Ingest JSON files
        logger.info("Vector store is empty. Processing JSON files...")
        json_files = list(Path('data').glob('extracted_data_*.json'))
        
        if not json_files:
            logger.warning("No JSON files found in data/ directory")
            logger.info("The chat system will work but with limited data.")
            logger.info("Make sure your extraction scripts have run and populated the data/ directory.")
            return False
        
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        # Ingest all JSON files
        ingested_count = vector_store.ingest_json_files('data')
        
        if ingested_count > 0:
            logger.info(f"✅ Successfully ingested {ingested_count} documents into vector store")
            
            # Display final stats
            final_stats = vector_store.get_stats()
            logger.info(f"Final vector store stats: {final_stats['total_documents']} total documents")
            return True
        else:
            logger.error("❌ Failed to ingest documents")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing vector store: {str(e)}")
        return False

def test_system_components():
    """Test that all system components work"""
    logger = logging.getLogger(__name__)
    
    logger.info("Testing system components...")
    
    try:
        # Test vector store
        from src.enhanced_vector_store import EnhancedVectorStore
        vector_store = EnhancedVectorStore()
        
        # Test retriever
        from src.smart_retriever import SmartRetriever
        retriever = SmartRetriever(vector_store)
        
        # Test response engine (without making actual LLM calls)
        from src.response_engine import ResponseEngine
        response_engine = ResponseEngine()
        
        logger.info("✅ All components initialized successfully")
        
        # Test a simple search
        results, context = retriever.search("test query", max_results=1)
        logger.info(f"✅ Search test completed - found {len(results)} results")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Component test failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    logger = setup_logging()
    
    logger.info("🚀 Starting K-Array Chat System Setup")
    logger.info("=" * 50)
    
    # Step 1: Check environment
    if not check_environment():
        logger.error("❌ Environment check failed. Please fix configuration and try again.")
        return False
    
    # Step 2: Setup directories
    setup_directories()
    
    # Step 3: Initialize vector store
    if not initialize_vector_store():
        logger.warning("⚠️ Vector store initialization had issues, but system can still run")
    
    # Step 4: Test components
    if not test_system_components():
        logger.error("❌ Component tests failed. System may not work properly.")
        return False
    
    logger.info("=" * 50)
    logger.info("✅ K-Array Chat System setup completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Make sure your API keys are set in the .env file")
    logger.info("2. Run: python k_array_chat.py")
    logger.info("3. Open http://localhost:7860 in your browser")
    logger.info("")
    logger.info("For help, check the CLAUDE.md file or the logs in data/")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)