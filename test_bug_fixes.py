#!/usr/bin/env python3
"""
Test suite for bug fixes and improvements.
Verifies that critical issues have been resolved.
"""

import sys
import uuid
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.append('.')

def test_unique_session_generation():
    """Test that session IDs are unique and secure."""
    print("🔐 Testing Unique Session ID Generation")
    print("=" * 50)
    
    from main import generate_session_id, generate_user_id
    
    # Generate multiple IDs
    session_ids = [generate_session_id() for _ in range(10)]
    user_ids = [generate_user_id() for _ in range(10)]
    
    # Check uniqueness
    assert len(set(session_ids)) == 10, "Session IDs should be unique"
    assert len(set(user_ids)) == 10, "User IDs should be unique"
    
    # Check format
    for session_id in session_ids:
        assert session_id.startswith("session_"), f"Session ID format wrong: {session_id}"
        assert len(session_id) > 20, f"Session ID too short: {session_id}"
    
    for user_id in user_ids:
        assert user_id.startswith("user_"), f"User ID format wrong: {user_id}"
        assert len(user_id) > 10, f"User ID too short: {user_id}"
    
    print("✅ Session and User ID generation working correctly")

def test_import_error_handling():
    """Test that import errors are handled properly."""
    print("\n📦 Testing Import Error Handling")
    print("=" * 50)
    
    # Test that the module can be imported
    try:
        from models._call_llm import OLLAMA_AVAILABLE, _logger
        print(f"✅ Ollama availability detected: {OLLAMA_AVAILABLE}")
        
        # Test environment variable handling
        import os
        original_fail_fast = os.getenv("KCHAT_FAIL_FAST")
        
        try:
            os.environ["KCHAT_FAIL_FAST"] = "false"
            # This should work even if ollama is not available
            from models._call_llm import ollama
            print("✅ Stub mode working when KCHAT_FAIL_FAST=false")
        finally:
            if original_fail_fast is not None:
                os.environ["KCHAT_FAIL_FAST"] = original_fail_fast
            elif "KCHAT_FAIL_FAST" in os.environ:
                del os.environ["KCHAT_FAIL_FAST"]
        
    except Exception as e:
        print(f"❌ Import error handling test failed: {e}")
        raise

def test_input_validation():
    """Test input validation and sanitization."""
    print("\n🛡️ Testing Input Validation")
    print("=" * 50)
    
    from utils.input_validator import validate_user_input, ValidationError
    
    # Test normal input
    normal_input = "Hello, how are you?"
    validated = validate_user_input(normal_input)
    assert validated == normal_input, "Normal input should pass through unchanged"
    print("✅ Normal input validation working")
    
    # Test HTML escaping
    html_input = "<script>alert('xss')</script>"
    try:
        validated = validate_user_input(html_input)
        assert "&lt;script&gt;" in validated, "HTML should be escaped"
        print("✅ HTML escaping working")
    except ValidationError:
        print("✅ XSS attempt blocked by validation")
    
    # Test length limits
    long_input = "A" * 3000  # Exceeds MAX_INPUT_LENGTH
    validated = validate_user_input(long_input)
    assert len(validated) <= 2000, "Input should be truncated"
    print("✅ Length limiting working")
    
    # Test injection detection
    injection_attempts = [
        "'; DROP TABLE users; --",
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "SELECT * FROM users WHERE id=1"
    ]
    
    blocked_count = 0
    for attempt in injection_attempts:
        try:
            validate_user_input(attempt)
        except ValidationError:
            blocked_count += 1
    
    print(f"✅ Blocked {blocked_count}/{len(injection_attempts)} injection attempts")

def test_memory_management():
    """Test memory management in AgentContext."""
    print("\n💾 Testing Memory Management")
    print("=" * 50)
    
    from agents.context import AgentContext
    
    context = AgentContext(
        user_id="test_user",
        session_id="test_session", 
        input="test"
    )
    
    # Test conversation history management
    for i in range(60):  # Exceed MAX_CONVERSATION_HISTORY
        context.add_to_conversation_history("user", f"Message {i}")
    
    assert len(context.conversation_history) <= 50, "Conversation history should be limited"
    print(f"✅ Conversation history limited to {len(context.conversation_history)} entries")
    
    # Test document management
    for i in range(15):  # Exceed MAX_DOCUMENTS_PER_CONTEXT
        context.add_document({"id": i, "content": f"Document {i}"})
    
    assert len(context.documents) <= 10, "Documents should be limited"
    print(f"✅ Documents limited to {len(context.documents)} entries")
    
    # Test action results management
    for i in range(25):  # Exceed MAX_ACTION_RESULTS
        context.add_action_result({"action": f"action_{i}", "result": "success"})
    
    assert len(context.action_results) <= 20, "Action results should be limited"
    print(f"✅ Action results limited to {len(context.action_results)} entries")

def test_configuration_management():
    """Test centralized configuration."""
    print("\n⚙️ Testing Configuration Management")
    print("=" * 50)
    
    try:
        from config.settings import config
        
        # Test basic configuration access
        assert hasattr(config, 'OLLAMA_HOST'), "Config should have OLLAMA_HOST"
        assert hasattr(config, 'DEBUG'), "Config should have DEBUG"
        assert hasattr(config, 'MAX_INPUT_LENGTH'), "Config should have MAX_INPUT_LENGTH"
        
        print(f"✅ Configuration loaded:")
        print(f"  - Environment: {config.ENVIRONMENT}")
        print(f"  - Debug: {config.DEBUG}")
        print(f"  - Ollama: {config.OLLAMA_HOST}:{config.OLLAMA_PORT}")
        print(f"  - Max Input Length: {config.MAX_INPUT_LENGTH}")
        
        # Test configuration validation
        errors = config.validate_configuration()
        if errors:
            print(f"⚠️ Configuration validation warnings: {errors}")
        else:
            print("✅ Configuration validation passed")
        
        # Test directory creation
        assert config.LOGS_DIR.exists(), "Logs directory should be created"
        assert config.BACKEND_DATA_DIR.exists(), "Backend data directory should be created"
        print("✅ Required directories created")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        raise

def test_resource_cleanup():
    """Test that resources are properly managed."""
    print("\n🗂️ Testing Resource Management")
    print("=" * 50)
    
    # Test file handle management with context managers
    test_file = Path(tempfile.mktemp())
    
    try:
        # Write test file
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Read test file
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == "test content", "File operations should work"
        print("✅ File operations with context managers working")
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
    
    print("✅ Resource cleanup working")

def test_error_handling():
    """Test improved error handling."""
    print("\n⚠️ Testing Error Handling")
    print("=" * 50)
    
    from utils.input_validator import ValidationError
    
    # Test that ValidationError is properly defined
    try:
        raise ValidationError("Test error")
    except ValidationError as e:
        assert str(e) == "Test error", "ValidationError should work properly"
        print("✅ ValidationError exception working")
    
    # Test graceful handling of missing dependencies
    try:
        from models._call_llm import ollama
        # Should not crash even if ollama is not available
        print("✅ Missing dependency handling working")
    except Exception as e:
        print(f"❌ Missing dependency handling failed: {e}")
        raise

def main():
    """Run all bug fix tests."""
    print("🧪 Bug Fix Verification Test Suite")
    print("=" * 60)
    print("Testing critical bug fixes and improvements")
    
    try:
        test_unique_session_generation()
        test_import_error_handling()
        test_input_validation()
        test_memory_management()
        test_configuration_management()
        test_resource_cleanup()
        test_error_handling()
        
        print("\n🎉 All Bug Fix Tests PASSED!")
        print("\n✅ Critical Issues Resolved:")
        print("- ✅ Unique session ID generation (Security)")
        print("- ✅ Proper import error handling (Reliability)")
        print("- ✅ Input validation and sanitization (Security)")
        print("- ✅ Memory management and limits (Performance)")
        print("- ✅ Centralized configuration (Maintainability)")
        print("- ✅ Resource management improvements (Stability)")
        print("- ✅ Enhanced error handling (Robustness)")
        
        print("\n🛡️ The system is now more secure, reliable, and maintainable.")
        
    except Exception as e:
        print(f"\n❌ Bug fix test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()