"""Tests for intent detection functionality."""

import pytest
from unittest.mock import patch, MagicMock

from intent_router import detect_intent
from config.intents_config import ALLOWED_INTENTS


class TestIntentDetection:
    """Test cases for intent detection."""

    def test_detect_intent_function_exists(self):
        """Test that detect_intent function is callable."""
        assert callable(detect_intent)

    @patch('intent_router.call_mistral')
    def test_detect_intent_technical_support(self, mock_call_mistral):
        """Test detection of technical support intent."""
        mock_call_mistral.return_value = "technical_support_request"
        
        result = detect_intent("My device is not working properly")
        
        assert result == "technical_support_request"
        assert result in ALLOWED_INTENTS
        mock_call_mistral.assert_called_once()

    @patch('intent_router.call_mistral')
    def test_detect_intent_product_information(self, mock_call_mistral):
        """Test detection of product information intent."""
        mock_call_mistral.return_value = "product_information_request"
        
        result = detect_intent("What are the specifications of this model?")
        
        assert result == "product_information_request"
        assert result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_cost_estimation(self, mock_call_mistral):
        """Test detection of cost estimation intent."""
        mock_call_mistral.return_value = "cost_estimation"
        
        result = detect_intent("Can you give me a quote for this service?")
        
        assert result == "cost_estimation"
        assert result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_booking_schedule(self, mock_call_mistral):
        """Test detection of booking/schedule intent."""
        mock_call_mistral.return_value = "booking_or_schedule"
        
        result = detect_intent("I would like to schedule an appointment")
        
        assert result == "booking_or_schedule"
        assert result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_document_request(self, mock_call_mistral):
        """Test detection of document request intent."""
        mock_call_mistral.return_value = "document_request"
        
        result = detect_intent("Could you send me the user manual?")
        
        assert result == "document_request"
        assert result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_open_ticket(self, mock_call_mistral):
        """Test detection of open ticket intent."""
        mock_call_mistral.return_value = "open_ticket"
        
        result = detect_intent("Please open a support ticket for this issue")
        
        assert result == "open_ticket"
        assert result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_complaint(self, mock_call_mistral):
        """Test detection of complaint intent."""
        mock_call_mistral.return_value = "complaint"
        
        result = detect_intent("I am very disappointed with this product")
        
        assert result == "complaint"
        assert result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_generic_smalltalk(self, mock_call_mistral):
        """Test detection of generic smalltalk intent."""
        mock_call_mistral.return_value = "generic_smalltalk"
        
        result = detect_intent("Hello, how are you today?")
        
        assert result == "generic_smalltalk"
        assert result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_llm_error_handling(self, mock_call_mistral):
        """Test handling of LLM errors during intent detection."""
        mock_call_mistral.side_effect = Exception("LLM connection failed")
        
        result = detect_intent("Test message")
        
        # Should return None or a default intent when LLM fails
        assert result is None or result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_invalid_response(self, mock_call_mistral):
        """Test handling of invalid LLM responses."""
        mock_call_mistral.return_value = "invalid_intent_name"
        
        result = detect_intent("Test message")
        
        # Should handle invalid intent gracefully
        assert result is None or result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_empty_input(self, mock_call_mistral):
        """Test handling of empty input."""
        mock_call_mistral.return_value = "generic_smalltalk"
        
        result = detect_intent("")
        
        # Should handle empty input gracefully
        assert result is None or result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_whitespace_input(self, mock_call_mistral):
        """Test handling of whitespace-only input."""
        mock_call_mistral.return_value = "generic_smalltalk"
        
        result = detect_intent("   ")
        
        # Should handle whitespace input gracefully
        assert result is None or result in ALLOWED_INTENTS

    @patch('intent_router.call_mistral')
    def test_detect_intent_very_long_input(self, mock_call_mistral):
        """Test handling of very long input."""
        long_input = "This is a very long message. " * 100
        mock_call_mistral.return_value = "technical_support_request"
        
        result = detect_intent(long_input)
        
        assert result == "technical_support_request"
        mock_call_mistral.assert_called_once()

    @patch('intent_router.call_mistral')
    def test_detect_intent_multilingual_input(self, mock_call_mistral):
        """Test handling of multilingual input."""
        multilingual_inputs = [
            "Ciao, come stai?",  # Italian
            "Hola, ¿cómo estás?",  # Spanish
            "Bonjour, comment allez-vous?",  # French
            "Hallo, wie geht es dir?",  # German
        ]
        
        mock_call_mistral.return_value = "generic_smalltalk"
        
        for text in multilingual_inputs:
            result = detect_intent(text)
            assert result == "generic_smalltalk"

    @patch('intent_router.call_mistral')
    def test_detect_intent_special_characters(self, mock_call_mistral):
        """Test handling of special characters and unicode."""
        special_inputs = [
            "Help! @#$%^&*()",
            "Price: €1,000.50",
            "Temperature: 25°C",
            "Email: test@example.com",
            "🚨 Emergency! 🚨"
        ]
        
        mock_call_mistral.return_value = "technical_support_request"
        
        for text in special_inputs:
            result = detect_intent(text)
            assert result in ALLOWED_INTENTS or result is None

    def test_allowed_intents_configuration(self):
        """Test that ALLOWED_INTENTS is properly configured."""
        assert isinstance(ALLOWED_INTENTS, set)
        assert len(ALLOWED_INTENTS) > 0
        
        # Check that all expected intents are present
        expected_intents = {
            "technical_support_request",
            "product_information_request", 
            "cost_estimation",
            "document_request",
            "booking_or_schedule",
            "open_ticket",
            "complaint",
            "generic_smalltalk"
        }
        
        assert expected_intents.issubset(ALLOWED_INTENTS)

    @patch('intent_router.call_mistral')
    def test_detect_intent_prompt_construction(self, mock_call_mistral):
        """Test that prompts are constructed properly for intent detection."""
        test_input = "I need help with my device"
        mock_call_mistral.return_value = "technical_support_request"
        
        detect_intent(test_input)
        
        # Verify that call_mistral was called with appropriate prompt
        mock_call_mistral.assert_called_once()
        call_args = mock_call_mistral.call_args[0][0]
        
        # Prompt should contain the input text and intent options
        assert test_input in call_args
        assert "technical_support_request" in call_args or "intent" in call_args.lower()

    @patch('intent_router.call_mistral')
    def test_detect_intent_case_sensitivity(self, mock_call_mistral):
        """Test that intent detection handles case variations."""
        test_cases = [
            "HELP ME WITH MY DEVICE",
            "help me with my device", 
            "Help Me With My Device",
            "hElP mE wItH mY dEvIcE"
        ]
        
        mock_call_mistral.return_value = "technical_support_request"
        
        for test_case in test_cases:
            result = detect_intent(test_case)
            assert result == "technical_support_request"