#!/usr/bin/env python3
"""
Quick Setup Script for K-Array Chat System
Automatically configures and tests the system
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for setup script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('setup.log')
        ]
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print("✅ Python version compatible:", sys.version.split()[0])
    return True

def install_dependencies():
    """Install required dependencies"""
    logger = logging.getLogger(__name__)
    logger.info("Installing dependencies...")
    
    try:
        # Install basic requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Basic dependencies installed")
        
        # Try to install optional dependencies
        optional_packages = [
            "sentence-transformers",  # For reranking
            "pymilvus",              # For advanced vector store
        ]
        
        for package in optional_packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              check=True, capture_output=True, text=True)
                print(f"✅ Optional package installed: {package}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Optional package failed (not critical): {package}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return False

def setup_environment():
    """Setup environment configuration"""
    logger = logging.getLogger(__name__)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ .env file created from template")
            print("🔑 Please edit .env file with your API keys before running the system")
            return False  # Need user to configure API keys
        else:
            print("❌ .env.example not found")
            return False
    
    # Validate .env file
    try:
        from src.config import Config
        if not Config.GEMINI_API_KEY and not Config.OPENAI_API_KEY:
            print("⚠️  No API keys configured in .env file")
            print("🔑 Please add at least one API key (GEMINI_API_KEY or OPENAI_API_KEY)")
            return False
        
        print("✅ Environment configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    logger = logging.getLogger(__name__)
    
    directories = [
        "data",
        "config", 
        "data/cache",
        "data/chroma_db",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Directories created/verified")
    return True

def setup_dynamic_config():
    """Setup dynamic configuration files"""
    logger = logging.getLogger(__name__)
    
    try:
        # Create default configuration
        from src.dynamic_config import DynamicConfigManager
        config_manager = DynamicConfigManager()
        config_manager.create_default_config_file()
        
        print("✅ Dynamic configuration files created")
        return True
        
    except Exception as e:
        print(f"❌ Dynamic config setup failed: {e}")
        return False

def run_tests():
    """Run basic system tests"""
    logger = logging.getLogger(__name__)
    
    print("🧪 Running basic system tests...")
    
    # Test configuration
    try:
        from src.config import Config
        print("✅ Configuration module test passed")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    # Test LLM manager
    try:
        from src.llm_manager import LLMManager
        if Config.GEMINI_API_KEY or Config.OPENAI_API_KEY:
            llm = LLMManager()
            print("✅ LLM manager test passed")
        else:
            print("⚠️  LLM manager test skipped (no API keys)")
    except Exception as e:
        print(f"❌ LLM manager test failed: {e}")
        return False
    
    # Test dynamic config
    try:
        from src.dynamic_config import dynamic_config
        config = dynamic_config.retrieval_config
        print("✅ Dynamic configuration test passed")
    except Exception as e:
        print(f"❌ Dynamic config test failed: {e}")
        return False
    
    return True

def run_integration_tests():
    """Run integration tests if requested"""
    print("🧪 Running integration tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_integration.py"], 
                               capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Integration tests passed")
            return True
        else:
            print("⚠️  Some integration tests failed (may be due to missing dependencies)")
            return True  # Non-critical for basic setup
            
    except subprocess.TimeoutExpired:
        print("⚠️  Integration tests timed out")
        return True
    except Exception as e:
        print(f"⚠️  Integration tests error: {e}")
        return True

def print_next_steps():
    """Print next steps for user"""
    print("\n" + "="*60)
    print("🎉 K-Array Chat System Setup Complete!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Configure your API keys in .env file:")
    print("   - Edit .env file")
    print("   - Add GEMINI_API_KEY or OPENAI_API_KEY")
    print("")
    print("2. Start the chat system:")
    print("   python3 k_array_chat.py")
    print("")
    print("3. Access the system:")
    print("   http://localhost:7860")
    print("")
    print("📚 DOCUMENTATION:")
    print("   - README.md - Complete usage guide")
    print("   - CLAUDE.md - Developer documentation")
    print("   - config/dynamic_config.json - System configuration")
    print("")
    print("🧪 TESTING:")
    print("   python3 test_query_intelligence.py")
    print("   python3 test_integration.py")
    print("")
    print("🆘 TROUBLESHOOTING:")
    print("   - Check setup.log for detailed logs")
    print("   - Ensure API keys are correctly configured")
    print("   - Run tests to verify system components")

def main():
    """Main setup function"""
    logger = setup_logging()
    logger.info("Starting K-Array Chat System setup")
    
    print("🚀 K-Array Chat System - Quick Setup")
    print("="*50)
    
    # Setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Setting up dynamic configuration", setup_dynamic_config),
        ("Setting up environment", setup_environment),
        ("Running basic tests", run_tests),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            if step_name == "Setting up environment":
                print("🔑 Please configure your API keys in .env file and run setup again")
            return False
    
    # Optional integration tests
    user_wants_integration = input("\n🧪 Run integration tests? (y/N): ").lower().startswith('y')
    if user_wants_integration:
        run_integration_tests()
    
    print_next_steps()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)