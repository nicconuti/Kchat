"""Tests for LLM client functionality."""

import pytest
from unittest.mock import patch, MagicMock, Mock
import time
import json

from models._call_llm import LLMClient, ModelName
from agents.context import AgentContext


class TestLLMClient:
    """Test cases for LLMClient."""

    @patch('models._call_llm.ollama')
    def test_llm_client_initialization(self, mock_ollama):
        """Test LLMClient initialization."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}, {'name': 'openchat'}]}
        
        client = LLMClient(default_model="mistral")
        
        assert client.default_model == "mistral"
        assert client.is_healthy is True
        assert 'mistral' in client.available_models
        mock_ollama.ps.assert_called_once()

    @patch('models._call_llm.ollama')
    def test_llm_client_initialization_failure(self, mock_ollama):
        """Test LLMClient initialization when Ollama is unavailable."""
        mock_ollama.ps.side_effect = Exception("Connection failed")
        
        # Should not raise exception (graceful degradation)
        client = LLMClient(default_model="mistral")
        
        assert client.is_healthy is False
        assert client.default_model == "mistral"

    @patch('models._call_llm.ollama')
    def test_health_check(self, mock_ollama):
        """Test health check functionality."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        client = LLMClient()
        
        # Initial health check should be true
        assert client._health_check() is True
        
        # Simulate Ollama going down
        mock_ollama.ps.side_effect = Exception("Connection lost")
        client.last_health_check = 0  # Force health check
        
        assert client._health_check() is False

    @patch('models._call_llm.ollama')
    def test_model_validation(self, mock_ollama):
        """Test model validation and fallback logic."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {
            'models': [
                {'name': 'mistral'}, 
                {'name': 'deepseek-r1:14b'},
                {'name': 'openchat'}
            ]
        }
        
        client = LLMClient(default_model="mistral")
        
        # Test exact match
        assert client._validate_model("mistral") == "mistral"
        
        # Test partial match
        assert client._validate_model("deepseek-r1:8b") == "deepseek-r1:14b"
        
        # Test fallback to default
        assert client._validate_model("nonexistent") == "mistral"

    @patch('models._call_llm.ollama')
    def test_call_basic(self, mock_ollama):
        """Test basic call functionality."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        mock_ollama.chat.return_value = {'message': {'content': 'Hello response'}}
        
        client = LLMClient()
        result = client.call("Hello", model="mistral")
        
        assert result == "Hello response"
        mock_ollama.chat.assert_called_once()

    @patch('models._call_llm.ollama')
    def test_call_with_system_prompt(self, mock_ollama):
        """Test call with system prompt."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        mock_ollama.chat.return_value = {'message': {'content': 'System response'}}
        
        client = LLMClient()
        client.call("Hello", system_prompt="You are a helpful assistant")
        
        # Verify system prompt was included
        call_args = mock_ollama.chat.call_args
        messages = call_args[1]['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == "You are a helpful assistant"

    @patch('models._call_llm.ollama')
    def test_call_with_retry(self, mock_ollama):
        """Test call with retry mechanism."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        # First call fails, second succeeds
        mock_ollama.chat.side_effect = [
            Exception("Temporary failure"),
            {'message': {'content': 'Success after retry'}}
        ]
        
        client = LLMClient(max_retries=2, retry_delay=0.1)
        result = client.call("Hello")
        
        assert result == "Success after retry"
        assert mock_ollama.chat.call_count == 2

    @patch('models._call_llm.ollama')
    def test_call_all_retries_fail(self, mock_ollama):
        """Test call when all retries fail."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        mock_ollama.chat.side_effect = Exception("Persistent failure")
        
        client = LLMClient(max_retries=2)
        result = client.call("Hello")
        
        # Should return empty string on failure
        assert result == ""

    @patch('models._call_llm.ollama')
    def test_stream_basic(self, mock_ollama):
        """Test basic streaming functionality."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        # Mock streaming response
        mock_stream = [
            {'message': {'content': 'Hello '}},
            {'message': {'content': 'world'}},
            {'message': {'content': '!'}}
        ]
        mock_ollama.chat.return_value = iter(mock_stream)
        
        client = LLMClient()
        chunks = list(client.stream("Hello", print_live=False))
        
        assert chunks == ['Hello ', 'world', '!']

    @patch('models._call_llm.ollama')
    def test_call_with_context(self, mock_ollama):
        """Test call_with_context functionality."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        mock_ollama.chat.return_value = {'message': {'content': 'Context response'}}
        
        client = LLMClient()
        context = AgentContext(
            session_id='test',
            user_id='test_user',
            input='Current input',
            conversation_history=[
                ('user', 'Previous user message'),
                ('assistant', 'Previous assistant response')
            ]
        )
        
        result = client.call_with_context("Current prompt", context)
        
        assert result == "Context response"
        
        # Verify conversation history was included
        call_args = mock_ollama.chat.call_args
        messages = call_args[1]['messages']
        
        # Should have history + current prompt
        assert len(messages) >= 3
        assert any('Previous user message' in str(msg) for msg in messages)

    @patch('models._call_llm.ollama')
    def test_conversation_history_management(self, mock_ollama):
        """Test conversation history management."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        client = LLMClient()
        context = AgentContext(
            session_id='test',
            user_id='test_user',
            input='test',
            conversation_history=[('user', 'msg' * 1000) for _ in range(50)]  # Very long history
        )
        
        # Should truncate history to manageable size
        client.manage_conversation_context(context, max_tokens_estimate=1000, max_turns=10)
        
        assert len(context.conversation_history) <= 10

    @patch('models._call_llm.ollama')
    def test_add_to_conversation_history(self, mock_ollama):
        """Test adding messages to conversation history."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        client = LLMClient()
        context = AgentContext(session_id='test', user_id='test_user', input='test')
        
        client.add_to_conversation_history(context, 'user', 'Hello')
        client.add_to_conversation_history(context, 'assistant', 'Hi there!')
        
        assert len(context.conversation_history) == 2
        assert context.conversation_history[0] == ('user', 'Hello')
        assert context.conversation_history[1] == ('assistant', 'Hi there!')

    @patch('models._call_llm.ollama')
    def test_get_conversation_summary(self, mock_ollama):
        """Test conversation summary generation."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        client = LLMClient()
        context = AgentContext(
            session_id='test',
            user_id='test_user',
            input='test',
            conversation_history=[
                ('user', 'Hello'),
                ('assistant', 'Hi there!'),
                ('user', 'How are you?'),
                ('assistant', 'I am fine, thank you!')
            ]
        )
        
        summary = client.get_conversation_summary(context)
        
        assert 'Hello' in summary
        assert 'Hi there!' in summary
        assert isinstance(summary, str)

    @patch('models._call_llm.ollama')
    def test_call_json_basic(self, mock_ollama):
        """Test call_json functionality."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        json_response = '[{"name": "test", "value": 123}]'
        mock_ollama.chat.return_value = {'message': {'content': json_response}}
        
        client = LLMClient()
        result = client.call_json("Extract data")
        
        assert result == [{"name": "test", "value": 123}]

    @patch('models._call_llm.ollama')
    def test_call_json_cleanup(self, mock_ollama):
        """Test call_json with messy response cleanup."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        messy_response = '```json\n[{"name": "test"}]\n```'
        mock_ollama.chat.return_value = {'message': {'content': messy_response}}
        
        client = LLMClient()
        result = client.call_json("Extract data")
        
        assert result == [{"name": "test"}]

    @patch('models._call_llm.ollama')
    def test_call_json_single_object_wrapping(self, mock_ollama):
        """Test call_json wraps single objects in array."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        single_object = '{"name": "test", "value": 123}'
        mock_ollama.chat.return_value = {'message': {'content': single_object}}
        
        client = LLMClient()
        result = client.call_json("Extract data")
        
        assert result == [{"name": "test", "value": 123}]

    @patch('models._call_llm.ollama')
    def test_call_json_invalid_response(self, mock_ollama):
        """Test call_json with invalid JSON response."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        invalid_response = 'This is not JSON'
        mock_ollama.chat.return_value = {'message': {'content': invalid_response}}
        
        client = LLMClient()
        result = client.call_json("Extract data")
        
        assert result is None

    def test_model_name_types(self):
        """Test ModelName type definition."""
        # Test that ModelName includes expected models
        valid_models = [
            "mistral",
            "openchat", 
            "deepseek-r1:8b",
            "deepseek-coder:6.7b-instruct",
            "deepseek-r1:14b",
            "llama3:8b-instruct"
        ]
        
        # This is more of a documentation test
        # In actual usage, TypeScript would enforce this
        for model in valid_models:
            assert isinstance(model, str)

    @patch('models._call_llm.ollama')
    def test_temperature_parameter(self, mock_ollama):
        """Test temperature parameter handling."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        mock_ollama.chat.return_value = {'message': {'content': 'response'}}
        
        client = LLMClient()
        client.call("Hello", temperature=0.5)
        
        call_args = mock_ollama.chat.call_args
        options = call_args[1]['options']
        assert options['temperature'] == 0.5

    @patch('models._call_llm.ollama')
    def test_timeout_handling(self, mock_ollama):
        """Test timeout handling in LLM calls."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        
        # Simulate timeout
        mock_ollama.chat.side_effect = TimeoutError("Request timed out")
        
        client = LLMClient(timeout=1.0)
        result = client.call("Hello")
        
        # Should handle timeout gracefully
        assert result == ""

    @patch('models._call_llm.ollama')
    def test_concurrent_calls(self, mock_ollama):
        """Test that client can handle concurrent calls."""
        mock_ollama.ps.return_value = {}
        mock_ollama.list.return_value = {'models': [{'name': 'mistral'}]}
        mock_ollama.chat.return_value = {'message': {'content': 'response'}}
        
        client = LLMClient()
        
        # Simulate multiple concurrent calls
        import threading
        
        results = []
        def make_call():
            result = client.call("Hello")
            results.append(result)
        
        threads = [threading.Thread(target=make_call) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all(result == "response" for result in results)