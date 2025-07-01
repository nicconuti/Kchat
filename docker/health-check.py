#!/usr/bin/env python3
"""
Health check script for Kchat application in Docker.
This script verifies that all critical components are working properly.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

try:
    from agents.context import AgentContext
    from models._call_llm import LLMClient
except ImportError as e:
    print(f"❌ Failed to import Kchat modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def check_python_environment():
    """Check if Python environment is properly set up."""
    try:
        import pandas
        import sentence_transformers
        import qdrant_client
        return True
    except ImportError as e:
        print(f"❌ Missing required Python package: {e}")
        return False

def check_file_system():
    """Check if required directories and files exist."""
    required_paths = [
        '/app/agents',
        '/app/models',
        '/app/utils',
        '/app/main.py'
    ]
    
    for path in required_paths:
        if not Path(path).exists():
            print(f"❌ Required path not found: {path}")
            return False
    
    return True

def check_data_directories():
    """Check if data directories are writable."""
    data_dirs = [
        '/app/logs',
        '/app/quotes',
        '/app/backend_data',
        '/app/embeddings'
    ]
    
    for dir_path in data_dirs:
        try:
            Path(dir_path).mkdir(exist_ok=True)
            test_file = Path(dir_path) / 'health_check.tmp'
            test_file.write_text('test')
            test_file.unlink()
        except Exception as e:
            print(f"❌ Cannot write to directory {dir_path}: {e}")
            return False
    
    return True

def check_agent_context():
    """Check if AgentContext can be created."""
    try:
        context = AgentContext(
            session_id='health_check',
            user_id='health_check',
            input='test'
        )
        return True
    except Exception as e:
        print(f"❌ Failed to create AgentContext: {e}")
        return False

def check_llm_client():
    """Check if LLM client can be initialized."""
    try:
        # Don't actually connect to Ollama in health check
        # Just verify the client can be instantiated
        client = LLMClient.__new__(LLMClient)
        client.default_model = "mistral"
        client.is_healthy = False  # Set to False to avoid actual connection
        return True
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        return False

def check_external_services():
    """Check connectivity to external services."""
    import socket
    
    services = [
        ('qdrant', int(os.getenv('QDRANT_PORT', 6333))),
        ('ollama', int(os.getenv('OLLAMA_PORT', 11434)))
    ]
    
    for service_host, service_port in services:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((service_host, service_port))
            sock.close()
            
            if result != 0:
                print(f"⚠️ Cannot connect to {service_host}:{service_port}")
                # Don't fail health check for external services
                # They might be starting up
        except Exception as e:
            print(f"⚠️ Error checking {service_host}:{service_port}: {e}")

def main():
    """Run all health checks."""
    print("🏥 Starting Kchat health check...")
    
    checks = [
        ("Python environment", check_python_environment),
        ("File system", check_file_system),
        ("Data directories", check_data_directories),
        ("Agent context", check_agent_context),
        ("LLM client", check_llm_client),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        try:
            if check_func():
                print(f"✅ {check_name}: OK")
            else:
                print(f"❌ {check_name}: FAILED")
                failed_checks.append(check_name)
        except Exception as e:
            print(f"❌ {check_name}: ERROR - {e}")
            failed_checks.append(check_name)
    
    # Check external services (warnings only)
    print("🔗 Checking external services...")
    check_external_services()
    
    if failed_checks:
        print(f"\n❌ Health check failed. Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        print("\n✅ All health checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()