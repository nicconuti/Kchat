"""
Input validation and sanitization utilities for Kchat.
Prevents injection attacks and ensures safe input processing.
"""

import re
import html
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Security constraints
MAX_INPUT_LENGTH = 2000
MAX_SESSION_ID_LENGTH = 100
MAX_USER_ID_LENGTH = 50
MIN_INPUT_LENGTH = 1

# Patterns for validation
SAFE_SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
SAFE_USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Dangerous patterns to filter
INJECTION_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # event handlers
    re.compile(r'data:text/html', re.IGNORECASE),
    re.compile(r'vbscript:', re.IGNORECASE),
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    re.compile(r'(\b(union|select|insert|update|delete|drop|create|alter)\b)', re.IGNORECASE),
    re.compile(r'(--|#|/\*|\*/)', re.IGNORECASE),
    re.compile(r"(';|'|\")", re.IGNORECASE),
]

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class InputValidator:
    """Validates and sanitizes user inputs for security."""
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, applies stricter validation rules
        """
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(__name__)
    
    def validate_user_input(self, text: str, allow_empty: bool = False) -> str:
        """
        Validate and sanitize user input text.
        
        Args:
            text: User input to validate
            allow_empty: Whether to allow empty input
            
        Returns:
            Sanitized text
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")
        
        # Check length constraints
        if not allow_empty and len(text.strip()) < MIN_INPUT_LENGTH:
            raise ValidationError("Input too short")
        
        if len(text) > MAX_INPUT_LENGTH:
            self.logger.warning(f"Input truncated from {len(text)} to {MAX_INPUT_LENGTH} characters")
            text = text[:MAX_INPUT_LENGTH]
        
        # Check for injection attempts
        self._check_for_injections(text)
        
        # Sanitize HTML entities
        sanitized = html.escape(text, quote=True)
        
        # Additional sanitization in strict mode
        if self.strict_mode:
            sanitized = self._strict_sanitize(sanitized)
        
        self.logger.debug(f"Input validated and sanitized: {len(sanitized)} chars")
        return sanitized.strip()
    
    def validate_session_id(self, session_id: str) -> str:
        """
        Validate session ID format and content.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Validated session ID
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(session_id, str):
            raise ValidationError("Session ID must be a string")
        
        if len(session_id) > MAX_SESSION_ID_LENGTH:
            raise ValidationError(f"Session ID too long (max {MAX_SESSION_ID_LENGTH})")
        
        if not SAFE_SESSION_ID_PATTERN.match(session_id):
            raise ValidationError("Session ID contains invalid characters")
        
        return session_id
    
    def validate_user_id(self, user_id: str) -> str:
        """
        Validate user ID format and content.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            Validated user ID
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(user_id, str):
            raise ValidationError("User ID must be a string")
        
        if len(user_id) > MAX_USER_ID_LENGTH:
            raise ValidationError(f"User ID too long (max {MAX_USER_ID_LENGTH})")
        
        if not SAFE_USER_ID_PATTERN.match(user_id):
            raise ValidationError("User ID contains invalid characters")
        
        return user_id
    
    def validate_file_path(self, file_path: str) -> str:
        """
        Validate file path for safety.
        
        Args:
            file_path: File path to validate
            
        Returns:
            Validated file path
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(file_path, str):
            raise ValidationError("File path must be a string")
        
        # Check for path traversal attempts
        if '..' in file_path or file_path.startswith('/'):
            raise ValidationError("Path traversal attempt detected")
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', '|', '&', ';', '`', '$']
        if any(char in file_path for char in dangerous_chars):
            raise ValidationError("File path contains dangerous characters")
        
        return file_path
    
    def _check_for_injections(self, text: str) -> None:
        """
        Check for various injection attack patterns.
        
        Args:
            text: Text to check
            
        Raises:
            ValidationError: If injection patterns found
        """
        # Check XSS patterns
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                self.logger.warning(f"XSS injection attempt detected: {pattern.pattern}")
                raise ValidationError("Potential XSS injection detected")
        
        # Check SQL injection patterns
        for pattern in SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                self.logger.warning(f"SQL injection attempt detected: {pattern.pattern}")
                raise ValidationError("Potential SQL injection detected")
    
    def _strict_sanitize(self, text: str) -> str:
        """
        Apply strict sanitization in strict mode.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Limit consecutive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove suspicious Unicode characters
        text = re.sub(r'[\u200B-\u200F\u2028\u2029\u202A-\u202E]', '', text)
        
        return text
    
    def sanitize_for_logging(self, text: str, max_length: int = 100) -> str:
        """
        Sanitize text for safe logging.
        
        Args:
            text: Text to sanitize
            max_length: Maximum length for log output
            
        Returns:
            Sanitized text safe for logging
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove potential secrets
        secret_patterns = [
            re.compile(r'\b[A-Za-z0-9+/]{20,}={0,2}\b'),  # Base64-like
            re.compile(r'\b[a-fA-F0-9]{32,}\b'),         # Hex tokens
            re.compile(r'\bsk-[a-zA-Z0-9]{20,}\b'),      # API keys
        ]
        
        sanitized = text
        for pattern in secret_patterns:
            sanitized = pattern.sub('[REDACTED]', sanitized)
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + '...'
        
        return sanitized

# Global validator instance
_default_validator = InputValidator(strict_mode=True)

# Convenience functions
def validate_user_input(text: str, allow_empty: bool = False) -> str:
    """Validate user input using default validator."""
    return _default_validator.validate_user_input(text, allow_empty)

def validate_session_id(session_id: str) -> str:
    """Validate session ID using default validator."""
    return _default_validator.validate_session_id(session_id)

def validate_user_id(user_id: str) -> str:
    """Validate user ID using default validator."""
    return _default_validator.validate_user_id(user_id)

def sanitize_for_logging(text: str, max_length: int = 100) -> str:
    """Sanitize text for logging using default validator."""
    return _default_validator.sanitize_for_logging(text, max_length)