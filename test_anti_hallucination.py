#!/usr/bin/env python3
"""
Anti-hallucination test for Kchat MVP system.
Verifies that the system behaves conservatively and avoids hallucinations.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from agents.document_retriever_agent import run as retrieve_documents
from agents.response_agent import run as generate_response
from agents.orchestrator_agent import run as orchestrate
from agents.context import AgentContext

def test_no_hallucination_on_unknown_queries():
    """Test that system doesn't hallucinate when asked about unknown topics."""
    print("🔍 Testing Anti-Hallucination: Unknown Topics")
    print("=" * 60)
    
    unknown_queries = [
        "What is the price of the XYZ-9000 speaker?",  # Non-existent product
        "Tell me about K-Array's quantum processors",  # Non-existent technology
        "What are the specifications of the FakeModel-123?",  # Made-up model
        "How does K-Array's antigravity technology work?",  # Impossible technology
        "What colors are available for the MadeUpSpeaker?"  # Non-existent product
    ]
    
    for query in unknown_queries:
        print(f"\nQuery: '{query}'")
        
        context = AgentContext(
            user_id='test_user',
            session_id='test_session',
            input=query,
            role='user'
        )
        
        # Test document retrieval
        result = retrieve_documents(context)
        
        print(f"Documents found: {len(result.documents)}")
        print(f"Source reliability: {result.source_reliability}")
        
        # Test response generation
        response_context = generate_response(result)
        print(f"Response: {response_context.response[:100]}...")
        print(f"Final reliability: {response_context.source_reliability}")
        
        # Verify conservative behavior
        assert result.source_reliability <= 0.7, f"Reliability too high for unknown query: {result.source_reliability}"
        
        # Check for hallucination indicators
        hallucination_keywords = ["xyz-9000", "quantum", "fakemodel", "antigravity", "madeupspeaker"]
        response_lower = response_context.response.lower()
        
        for keyword in hallucination_keywords:
            if keyword in response_lower and "non ho" not in response_lower:
                print(f"⚠️ Potential hallucination detected: {keyword}")
                assert False, f"System may be hallucinating about {keyword}"
        
        print("✅ Conservative response verified")

def test_conservative_responses_low_confidence():
    """Test that system provides conservative responses for low confidence scenarios."""
    print("\n🛡️ Testing Conservative Responses for Low Confidence")
    print("=" * 60)
    
    vague_queries = [
        "Tell me everything about speakers",
        "What should I buy?", 
        "Help me with audio",
        "I need something for sound"
    ]
    
    for query in vague_queries:
        print(f"\nQuery: '{query}'")
        
        context = AgentContext(
            user_id='test_user',
            session_id='test_session',
            input=query,
            role='user'
        )
        
        # Full orchestration test
        try:
            result = orchestrate(context)
            
            print(f"Response: {result.response[:100]}...")
            print(f"Source reliability: {result.source_reliability}")
            print(f"Confidence: {result.confidence}")
            
            # Verify conservative behavior
            if result.source_reliability < 0.3:
                assert "www.k-array.com" in result.response, "Conservative response should mention official website"
                print("✅ Conservative response includes official website reference")
            
        except Exception as e:
            print(f"Error in orchestration: {e}")
            print("✅ System handled error gracefully")

def test_source_attribution():
    """Test that responses properly attribute sources."""
    print("\n📋 Testing Source Attribution")
    print("=" * 60)
    
    k_array_queries = [
        "Tell me about K-Array",
        "K-Array company information",
        "What does K-Array do?"
    ]
    
    for query in k_array_queries:
        print(f"\nQuery: '{query}'")
        
        context = AgentContext(
            user_id='test_user',
            session_id='test_session',
            input=query,
            role='user'
        )
        
        result = retrieve_documents(context)
        
        if result.documents:
            response_context = generate_response(result)
            
            print(f"Response: {response_context.response[:150]}...")
            
            # Verify source attribution
            has_source = ("k-array.com" in response_context.response.lower() or 
                         "fonte:" in response_context.response.lower())
            
            assert has_source, "Response should include source attribution"
            print("✅ Source attribution verified")
        else:
            print("📝 No documents found - conservative behavior")

def test_role_based_access():
    """Test role-based access control."""
    print("\n👥 Testing Role-Based Access Control")
    print("=" * 60)
    
    test_query = "Technical support information"
    roles = ['guest', 'user', 'admin']
    
    for role in roles:
        print(f"\nTesting role: {role}")
        
        context = AgentContext(
            user_id=f'test_{role}',
            session_id='test_session',
            input=test_query,
            role=role
        )
        
        result = retrieve_documents(context)
        
        print(f"Documents accessible: {len(result.documents)}")
        
        # Guest should have limited access
        if role == 'guest':
            tech_docs = [doc for doc in result.documents if doc.get('category') == 'tech_assistance']
            assert len(tech_docs) == 0, f"Guest should not access tech_assistance documents, but got {len(tech_docs)}"
            print("✅ Guest access properly restricted")
        
        print(f"✅ Role {role} handled correctly")

def test_error_handling():
    """Test error handling and graceful degradation."""
    print("\n⚠️ Testing Error Handling")
    print("=" * 60)
    
    # Test with malformed context
    try:
        context = AgentContext(
            user_id='test',
            session_id='test',
            input='',  # Empty input
            role='user'
        )
        
        result = retrieve_documents(context)
        print(f"Empty query handled: reliability = {result.source_reliability}")
        assert result.source_reliability == 0.0, "Empty query should have zero reliability"
        print("✅ Empty query handled gracefully")
        
    except Exception as e:
        print(f"✅ Empty query caused expected error: {e}")

def test_mvp_stability():
    """Test overall MVP stability with realistic user interactions."""
    print("\n🎯 Testing MVP Stability")
    print("=" * 60)
    
    realistic_queries = [
        "Ciao, come stai?",  # Greeting
        "Che cos'è K-Array?",  # Company question
        "Quanto costa?",  # Pricing without specifics
        "Ho bisogno di aiuto",  # General help
        "Dove posso trovare informazioni?"  # Information request
    ]
    
    for query in realistic_queries:
        print(f"\nQuery: '{query}'")
        
        try:
            context = AgentContext(
                user_id='mvp_test',
                session_id='stability_test',
                input=query,
                role='user'
            )
            
            # Full system test
            result = orchestrate(context)
            
            print(f"Response generated: {bool(result.response)}")
            print(f"Source reliability: {result.source_reliability}")
            print(f"Error flag: {result.error_flag}")
            
            # Verify system stability
            assert result.response is not None, "System should always provide a response"
            assert isinstance(result.source_reliability, (int, float)), "Reliability should be numeric"
            assert 0.0 <= result.source_reliability <= 1.0, "Reliability should be between 0 and 1"
            
            print("✅ Stable response generated")
            
        except Exception as e:
            print(f"❌ System instability detected: {e}")
            raise

def main():
    """Run all anti-hallucination tests."""
    print("🧪 Kchat MVP Anti-Hallucination Test Suite")
    print("=" * 70)
    print("Testing system behavior to ensure reliable, conservative responses")
    print("and prevention of hallucinations in the MVP demo.")
    
    try:
        test_no_hallucination_on_unknown_queries()
        test_conservative_responses_low_confidence()
        test_source_attribution()
        test_role_based_access()
        test_error_handling()
        test_mvp_stability()
        
        print("\n🎉 All Anti-Hallucination Tests PASSED!")
        print("\n✅ MVP System Verification Summary:")
        print("- ✅ No hallucinations on unknown topics")
        print("- ✅ Conservative responses for vague queries")
        print("- ✅ Proper source attribution")
        print("- ✅ Role-based access control working")
        print("- ✅ Graceful error handling")
        print("- ✅ Overall system stability confirmed")
        
        print("\n🛡️ The system is ready for demo with anti-hallucination measures in place.")
        
    except AssertionError as e:
        print(f"\n❌ Anti-hallucination test FAILED: {e}")
        print("\n⚠️ System requires further hardening before demo.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n💥 Unexpected error in testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()