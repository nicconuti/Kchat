"""Tests for main application entry point."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from agents.context import AgentContext
from main import main


class TestMainApplication:
    """Test cases for the main application."""

    @patch('builtins.input')
    @patch('main.orchestrate')
    def test_main_single_interaction(self, mock_orchestrate, mock_input):
        """Test main function with single user interaction."""
        # Setup
        mock_input.side_effect = ["Hello", "exit"]
        mock_context = AgentContext(session_id='test', user_id="test_user", input="Hello")
        mock_context.response = "Hello! How can I help you?"
        mock_orchestrate.return_value = mock_context
        
        # Capture stdout
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            main()  # main() should complete normally when exit is entered
        
        # Verify
        assert mock_orchestrate.called
        output = captured_output.getvalue()
        assert "💬 Kchat" in output
        assert "Hello! How can I help you?" in output

    @patch('builtins.input')
    @patch('main.orchestrate')
    def test_main_multiple_interactions(self, mock_orchestrate, mock_input):
        """Test main function with multiple interactions."""
        # Setup
        mock_input.side_effect = ["First message", "Second message", "quit"]
        
        responses = [
            AgentContext(session_id='test', user_id="test_user", input="First message", response="First response"),
            AgentContext(session_id='test', user_id="test_user", input="Second message", response="Second response")
        ]
        mock_orchestrate.side_effect = responses
        
        # Execute
        main()
        
        # Verify
        assert mock_orchestrate.call_count == 2

    @patch('builtins.input')
    @patch('main.orchestrate')
    def test_main_handles_orchestration_error(self, mock_orchestrate, mock_input):
        """Test main function handles orchestration errors gracefully."""
        # Setup
        mock_input.side_effect = ["Error message", "exit"]
        mock_orchestrate.side_effect = Exception("Orchestration failed")
        
        # Execute - should not crash
        main()
        
        # Verify orchestration was attempted
        assert mock_orchestrate.called

    @patch('builtins.input')
    def test_main_exit_commands(self, mock_input):
        """Test that various exit commands work."""
        exit_commands = ["exit", "quit", "EXIT", "QUIT"]
        
        for exit_cmd in exit_commands:
            mock_input.side_effect = [exit_cmd]
            
            main()

    @patch('builtins.input')
    @patch('main.orchestrate')
    def test_main_empty_input_handling(self, mock_orchestrate, mock_input):
        """Test handling of empty input."""
        # Setup
        mock_input.side_effect = ["", "   ", "actual message", "exit"]
        mock_context = AgentContext(session_id='test', user_id="test_user", input="")
        mock_context.response = "Response to actual message"
        
        # Return different responses for different calls
        def side_effect(ctx):
            if ctx.input == "":
                ctx.response = "Empty response"
            elif ctx.input == "   ":
                ctx.response = "Whitespace response"
            else:
                ctx.response = "Response to actual message"
            return ctx
        
        mock_orchestrate.side_effect = side_effect
        
        # Execute
        main()
        
        # Verify - should orchestrate for all inputs (including empty ones)
        assert mock_orchestrate.call_count == 3

    @patch('builtins.input')
    @patch('main.orchestrate')
    def test_main_context_initialization(self, mock_orchestrate, mock_input):
        """Test that context is properly initialized."""
        # Setup
        mock_input.side_effect = ["test message", "exit"]
        mock_orchestrate.return_value = AgentContext(
            session_id='test', 
            user_id="test_user", 
            input="test message",
            response="test response"
        )
        
        # Execute
        main()
        
        # Verify context initialization
        call_args = mock_orchestrate.call_args[0][0]
        assert call_args.session_id == 'qwerty'  # From main.py
        assert call_args.user_id == "power_user"  # From main.py
        assert call_args.input == "test message"

    def test_main_imports(self):
        """Test that main module imports are working."""
        # This test ensures all required imports are available
        from main import main
        from agents.context import AgentContext
        from agents.orchestrator_agent import run as orchestrate
        
        assert callable(main)
        assert AgentContext is not None
        assert callable(orchestrate)

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_main_keyboard_interrupt(self, mock_input):
        """Test graceful handling of KeyboardInterrupt (Ctrl+C)."""
        # Should handle Ctrl+C gracefully
        with pytest.raises(KeyboardInterrupt):
            main()

    @patch('builtins.input')
    @patch('main.orchestrate')
    def test_main_unicode_input(self, mock_orchestrate, mock_input):
        """Test handling of unicode input."""
        # Setup
        unicode_message = "Ciao! Come stai? 🤖"
        mock_input.side_effect = [unicode_message, "exit"]
        mock_context = AgentContext(session_id='test', user_id="test_user", input=unicode_message)
        mock_context.response = "Ciao! Sto bene, grazie! 😊"
        mock_orchestrate.return_value = mock_context
        
        # Execute
        main()
        
        # Verify unicode handling
        assert mock_orchestrate.called
        call_args = mock_orchestrate.call_args[0][0]
        assert call_args.input == unicode_message