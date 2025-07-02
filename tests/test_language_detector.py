"""Tests for language detection functionality."""

import pytest
from unittest.mock import patch, MagicMock

from language_detector import detect_language


class TestLanguageDetection:
    """Test cases for language detection."""

    def test_detect_language_function_exists(self):
        """Test that detect_language function is callable."""
        assert callable(detect_language)

    @patch('language_detector.call_mistral')
    def test_detect_language_english(self, mock_call_mistral):
        """Test detection of English language."""
        mock_call_mistral.return_value = "en"
        
        result = detect_language("Hello, how are you today?")
        
        assert result == "en"
        mock_call_mistral.assert_called_once()

    @patch('language_detector.call_mistral')
    def test_detect_language_italian(self, mock_call_mistral):
        """Test detection of Italian language."""
        mock_call_mistral.return_value = "it"
        
        result = detect_language("Ciao, come stai oggi?")
        
        assert result == "it"

    @patch('language_detector.call_mistral')
    def test_detect_language_spanish(self, mock_call_mistral):
        """Test detection of Spanish language."""
        mock_call_mistral.return_value = "es"
        
        result = detect_language("Hola, ¿cómo estás hoy?")
        
        assert result == "es"

    @patch('language_detector.call_mistral')
    def test_detect_language_french(self, mock_call_mistral):
        """Test detection of French language."""
        mock_call_mistral.return_value = "fr"
        
        result = detect_language("Bonjour, comment allez-vous aujourd'hui?")
        
        assert result == "fr"

    @patch('language_detector.call_mistral')
    def test_detect_language_german(self, mock_call_mistral):
        """Test detection of German language."""
        mock_call_mistral.return_value = "de"
        
        result = detect_language("Hallo, wie geht es dir heute?")
        
        assert result == "de"

    @patch('language_detector.call_mistral')
    def test_detect_language_llm_error_handling(self, mock_call_mistral):
        """Test handling of LLM errors during language detection."""
        mock_call_mistral.side_effect = Exception("LLM connection failed")
        
        result = detect_language("Test message")
        
        # Should return a default language (likely 'en') when LLM fails
        assert isinstance(result, str)
        assert len(result) == 2  # ISO 639-1 codes are 2 characters

    @patch('language_detector.call_mistral')
    def test_detect_language_invalid_response(self, mock_call_mistral):
        """Test handling of invalid LLM responses."""
        mock_call_mistral.return_value = "invalid_language_code"
        
        result = detect_language("Test message")
        
        # Should handle invalid language codes gracefully
        assert isinstance(result, str)
        # Should either return a valid ISO code or default to 'en'
        assert len(result) >= 2

    @patch('language_detector.call_mistral')
    def test_detect_language_empty_input(self, mock_call_mistral):
        """Test handling of empty input."""
        mock_call_mistral.return_value = "en"
        
        result = detect_language("")
        
        # Should handle empty input gracefully, likely defaulting to English
        assert result == "en"

    @patch('language_detector.call_mistral')
    def test_detect_language_whitespace_input(self, mock_call_mistral):
        """Test handling of whitespace-only input."""
        mock_call_mistral.return_value = "en"
        
        result = detect_language("   ")
        
        # Should handle whitespace input gracefully
        assert result == "en"

    @patch('language_detector.call_mistral')
    def test_detect_language_mixed_languages(self, mock_call_mistral):
        """Test detection of mixed language input."""
        # Test input with English and Italian
        mixed_input = "Hello ciao, how are you come stai?"
        mock_call_mistral.return_value = "en"  # Should detect primary language
        
        result = detect_language(mixed_input)
        
        assert result in ["en", "it"]  # Should detect one of the languages

    @patch('language_detector.call_mistral')
    def test_detect_language_technical_terms(self, mock_call_mistral):
        """Test detection with technical terms and proper nouns."""
        technical_input = "The API endpoint returns JSON data with UTF-8 encoding"
        mock_call_mistral.return_value = "en"
        
        result = detect_language(technical_input)
        
        assert result == "en"

    @patch('language_detector.call_mistral')
    def test_detect_language_numbers_and_symbols(self, mock_call_mistral):
        """Test detection with numbers and symbols."""
        numeric_input = "Price: €1,250.50 (including 22% VAT)"
        mock_call_mistral.return_value = "en"
        
        result = detect_language(numeric_input)
        
        assert result == "en"

    @patch('language_detector.call_mistral')
    def test_detect_language_very_short_input(self, mock_call_mistral):
        """Test detection with very short input."""
        short_inputs = ["Hi", "Sì", "Ok", "No", "?"]
        mock_call_mistral.return_value = "en"
        
        for short_input in short_inputs:
            result = detect_language(short_input)
            assert isinstance(result, str)
            assert len(result) >= 2

    @patch('language_detector.call_mistral')
    def test_detect_language_very_long_input(self, mock_call_mistral):
        """Test detection with very long input."""
        long_input = "This is a very long English sentence. " * 100
        mock_call_mistral.return_value = "en"
        
        result = detect_language(long_input)
        
        assert result == "en"

    @patch('language_detector.call_mistral')
    def test_detect_language_unicode_characters(self, mock_call_mistral):
        """Test detection with unicode characters and emojis."""
        unicode_inputs = [
            "Hello! 😊 How are you?",
            "Température: 25°C",
            "Naïve café résumé",
            "München Straße",
            "北京 (Beijing)"
        ]
        
        mock_call_mistral.return_value = "en"
        
        for unicode_input in unicode_inputs:
            result = detect_language(unicode_input)
            assert isinstance(result, str)

    @patch('language_detector.call_mistral')
    def test_detect_language_code_and_markup(self, mock_call_mistral):
        """Test detection with code snippets and markup."""
        code_inputs = [
            "def hello(): print('Hello world')",
            "<html><body>Hello</body></html>",
            "SELECT * FROM users WHERE id = 1",
            "console.log('Hello world');"
        ]
        
        mock_call_mistral.return_value = "en"
        
        for code_input in code_inputs:
            result = detect_language(code_input)
            assert isinstance(result, str)

    @patch('language_detector.call_mistral')
    def test_detect_language_prompt_construction(self, mock_call_mistral):
        """Test that prompts are constructed properly for language detection."""
        test_input = "Ciao, come stai?"
        mock_call_mistral.return_value = "it"
        
        detect_language(test_input)
        
        # Verify that call_mistral was called with appropriate prompt
        mock_call_mistral.assert_called_once()
        call_args = mock_call_mistral.call_args[0][0]
        
        # Prompt should contain the input text and language detection instructions
        assert test_input in call_args
        assert any(word in call_args.lower() for word in ["language", "lingua", "detect", "identify"])

    @patch('language_detector.call_mistral')
    def test_detect_language_iso_code_format(self, mock_call_mistral):
        """Test that returned language codes follow ISO 639-1 format."""
        valid_iso_codes = ["en", "it", "es", "fr", "de", "pt", "ru", "zh", "ja", "ko"]
        
        for iso_code in valid_iso_codes:
            mock_call_mistral.return_value = iso_code
            result = detect_language("Test input")
            assert result == iso_code
            assert len(result) == 2
            assert result.islower()

    @patch('language_detector.call_mistral')
    def test_detect_language_case_insensitive_response(self, mock_call_mistral):
        """Test that function handles case variations in LLM response."""
        case_variations = ["EN", "en", "En", "eN"]
        
        for variation in case_variations:
            mock_call_mistral.return_value = variation
            result = detect_language("Hello world")
            # Result should be normalized to lowercase
            assert result.lower() == "en"

    @patch('language_detector.call_mistral')
    def test_detect_language_response_cleanup(self, mock_call_mistral):
        """Test that function cleans up LLM responses properly."""
        messy_responses = [
            " en ",
            "en\n",
            "Language: en",
            "The language is: en",
            "en."
        ]
        
        for messy_response in messy_responses:
            mock_call_mistral.return_value = messy_response
            result = detect_language("Hello world")
            # Should extract clean language code
            assert "en" in result.lower()

    @patch('language_detector.call_mistral')
    def test_detect_language_consistency(self, mock_call_mistral):
        """Test that similar inputs produce consistent results."""
        similar_inputs = [
            "Hello, how are you?",
            "Hi, how are you doing?",
            "Hello there, how are you today?"
        ]
        
        mock_call_mistral.return_value = "en"
        
        results = [detect_language(text) for text in similar_inputs]
        
        # All similar English inputs should return the same language code
        assert all(result == "en" for result in results)