"""
Centralized configuration management for Kchat.
Handles environment variables, defaults, and validation.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class KchatConfig:
    """Centralized configuration for Kchat system."""
    
    def __init__(self):
        """Initialize configuration from environment variables and defaults."""
        
        # === SYSTEM CONFIGURATION ===
        self.DEBUG = self._get_bool_env("KCHAT_DEBUG", False)
        self.ENVIRONMENT = self._get_env("KCHAT_ENVIRONMENT", "development")
        self.LOG_LEVEL = self._get_env("KCHAT_LOG_LEVEL", "INFO")
        
        # === SECURITY CONFIGURATION ===
        self.FAIL_FAST_ON_MISSING_DEPS = self._get_bool_env("KCHAT_FAIL_FAST", False)
        self.STRICT_INPUT_VALIDATION = self._get_bool_env("KCHAT_STRICT_VALIDATION", True)
        self.MAX_INPUT_LENGTH = self._get_int_env("KCHAT_MAX_INPUT_LENGTH", 2000)
        self.MAX_SESSION_DURATION_HOURS = self._get_int_env("KCHAT_MAX_SESSION_HOURS", 24)
        
        # === MEMORY MANAGEMENT ===
        self.MAX_CONVERSATION_HISTORY = self._get_int_env("KCHAT_MAX_CONVERSATION_HISTORY", 50)
        self.MAX_DOCUMENTS_PER_CONTEXT = self._get_int_env("KCHAT_MAX_DOCUMENTS", 10)
        self.MAX_ACTION_RESULTS = self._get_int_env("KCHAT_MAX_ACTION_RESULTS", 20)
        
        # === LLM CONFIGURATION ===
        self.OLLAMA_HOST = self._get_env("OLLAMA_HOST", "localhost")
        self.OLLAMA_PORT = self._get_int_env("OLLAMA_PORT", 11434)
        self.OLLAMA_TIMEOUT = self._get_int_env("OLLAMA_TIMEOUT", 60)
        self.DEFAULT_LLM_MODEL = self._get_env("KCHAT_DEFAULT_MODEL", "mistral")
        self.FALLBACK_LLM_MODEL = self._get_env("KCHAT_FALLBACK_MODEL", "openchat")
        
        # === RAG CONFIGURATION ===
        self.QDRANT_HOST = self._get_env("QDRANT_HOST", "localhost")
        self.QDRANT_PORT = self._get_int_env("QDRANT_PORT", 6333)
        self.QDRANT_TIMEOUT = self._get_int_env("QDRANT_TIMEOUT", 30)
        self.EMBEDDING_MODEL = self._get_env("KCHAT_EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
        self.CROSS_ENCODER_MODEL = self._get_env("KCHAT_CROSS_ENCODER", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # === CONFIDENCE THRESHOLDS ===
        self.MIN_CROSS_ENCODER_SCORE = self._get_float_env("KCHAT_MIN_CROSS_SCORE", 0.3)
        self.MIN_COSINE_SIMILARITY = self._get_float_env("KCHAT_MIN_COSINE_SIM", 0.2)
        self.MIN_FINAL_SCORE = self._get_float_env("KCHAT_MIN_FINAL_SCORE", 0.4)
        self.MIN_SOURCE_RELIABILITY = self._get_float_env("KCHAT_MIN_SOURCE_RELIABILITY", 0.3)
        
        # === FILE PATHS ===
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / self._get_env("KCHAT_DATA_DIR", "data")
        self.LOGS_DIR = self.BASE_DIR / self._get_env("KCHAT_LOGS_DIR", "logs")
        self.BACKEND_DATA_DIR = self.BASE_DIR / self._get_env("KCHAT_BACKEND_DATA_DIR", "backend_data")
        self.QUOTES_DIR = self.BASE_DIR / self._get_env("KCHAT_QUOTES_DIR", "quotes")
        self.EMBEDDINGS_DIR = self.BASE_DIR / self._get_env("KCHAT_EMBEDDINGS_DIR", "embeddings")
        
        # === KNOWLEDGE BASE PATHS ===
        self.KARRAY_DATA_DIR = self.BASE_DIR / "karray_rag" / "data"
        self.KNOWLEDGE_BASE_FILE = self.KARRAY_DATA_DIR / "embedded_karray_documents.jsonl"
        self.QUARANTINE_DIR = self.BASE_DIR / "quarantine"
        
        # === PDF GENERATION ===
        self.PDF_TEMPLATE_DIR = self.BASE_DIR / "templates"
        self.PDF_COMPANY_NAME = self._get_env("KCHAT_COMPANY_NAME", "K-Array")
        self.PDF_COMPANY_URL = self._get_env("KCHAT_COMPANY_URL", "www.k-array.com")
        
        # === LOGGING CONFIGURATION ===
        self.LOG_FORMAT = self._get_env("KCHAT_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.LOG_FILE_MAX_SIZE = self._get_int_env("KCHAT_LOG_MAX_SIZE", 10485760)  # 10MB
        self.LOG_BACKUP_COUNT = self._get_int_env("KCHAT_LOG_BACKUP_COUNT", 5)
        
        # === RATE LIMITING ===
        self.RATE_LIMIT_REQUESTS_PER_MINUTE = self._get_int_env("KCHAT_RATE_LIMIT_RPM", 60)
        self.RATE_LIMIT_REQUESTS_PER_HOUR = self._get_int_env("KCHAT_RATE_LIMIT_RPH", 1000)
        
        # Create required directories
        self._create_directories()
        
        # Log configuration if debug mode
        if self.DEBUG:
            self._log_configuration()
    
    def _get_env(self, key: str, default: str) -> str:
        """Get string environment variable with default."""
        return os.getenv(key, default)
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable with default."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default
    
    def _get_float_env(self, key: str, default: float) -> float:
        """Get float environment variable with default."""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid float value for {key}, using default: {default}")
            return default
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable with default."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _create_directories(self) -> None:
        """Create required directories if they don't exist."""
        directories = [
            self.DATA_DIR,
            self.LOGS_DIR,
            self.BACKEND_DATA_DIR,
            self.QUOTES_DIR,
            self.EMBEDDINGS_DIR,
            self.KARRAY_DATA_DIR,
            self.QUARANTINE_DIR
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
    
    def _log_configuration(self) -> None:
        """Log current configuration in debug mode."""
        logger.debug("=== KCHAT CONFIGURATION ===")
        logger.debug(f"Environment: {self.ENVIRONMENT}")
        logger.debug(f"Debug Mode: {self.DEBUG}")
        logger.debug(f"Ollama: {self.OLLAMA_HOST}:{self.OLLAMA_PORT}")
        logger.debug(f"Qdrant: {self.QDRANT_HOST}:{self.QDRANT_PORT}")
        logger.debug(f"Default Model: {self.DEFAULT_LLM_MODEL}")
        logger.debug(f"Base Directory: {self.BASE_DIR}")
        logger.debug("========================")
    
    def get_ollama_url(self) -> str:
        """Get complete Ollama URL."""
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"
    
    def get_qdrant_url(self) -> str:
        """Get complete Qdrant URL."""
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    def get_backend_subdirs(self) -> Dict[str, Path]:
        """Get backend data subdirectories."""
        subdirs = {}
        for subdir in ["tickets", "appointments", "complaints", "quotes"]:
            path = self.BACKEND_DATA_DIR / subdir
            path.mkdir(exist_ok=True)
            subdirs[subdir] = path
        return subdirs
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate thresholds
        if not 0.0 <= self.MIN_CROSS_ENCODER_SCORE <= 1.0:
            errors.append("MIN_CROSS_ENCODER_SCORE must be between 0.0 and 1.0")
        
        if not 0.0 <= self.MIN_COSINE_SIMILARITY <= 1.0:
            errors.append("MIN_COSINE_SIMILARITY must be between 0.0 and 1.0")
        
        if not 0.0 <= self.MIN_SOURCE_RELIABILITY <= 1.0:
            errors.append("MIN_SOURCE_RELIABILITY must be between 0.0 and 1.0")
        
        # Validate memory limits
        if self.MAX_INPUT_LENGTH < 1:
            errors.append("MAX_INPUT_LENGTH must be positive")
        
        if self.MAX_CONVERSATION_HISTORY < 1:
            errors.append("MAX_CONVERSATION_HISTORY must be positive")
        
        # Validate network settings
        if not 1 <= self.OLLAMA_PORT <= 65535:
            errors.append("OLLAMA_PORT must be between 1 and 65535")
        
        if not 1 <= self.QDRANT_PORT <= 65535:
            errors.append("QDRANT_PORT must be between 1 and 65535")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for logging/debugging)."""
        return {
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "ollama_host": self.OLLAMA_HOST,
            "ollama_port": self.OLLAMA_PORT,
            "qdrant_host": self.QDRANT_HOST,
            "qdrant_port": self.QDRANT_PORT,
            "default_model": self.DEFAULT_LLM_MODEL,
            "max_input_length": self.MAX_INPUT_LENGTH,
            "min_source_reliability": self.MIN_SOURCE_RELIABILITY,
            "strict_validation": self.STRICT_INPUT_VALIDATION
        }

# Global configuration instance
config = KchatConfig()

# Validate configuration on import
config_errors = config.validate_configuration()
if config_errors:
    for error in config_errors:
        logger.error(f"Configuration error: {error}")
    
    if config.is_production():
        raise ValueError(f"Invalid production configuration: {config_errors}")
    else:
        logger.warning("Configuration errors detected in development mode")

# Export commonly used values
DEBUG = config.DEBUG
ENVIRONMENT = config.ENVIRONMENT
BASE_DIR = config.BASE_DIR
LOGS_DIR = config.LOGS_DIR
BACKEND_DATA_DIR = config.BACKEND_DATA_DIR