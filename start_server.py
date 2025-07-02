#!/usr/bin/env python3
"""
Start script for K-Array Chat API server.
Handles setup and graceful startup.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Set up basic logging before importing other modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("start_server")

# Ensure current directory is in sys.path
sys.path.append(str(Path(__file__).parent.resolve()))

try:
    from config.settings import config
except ImportError:
    logger.warning("Could not import config, using defaults")

    class MockConfig:
        DEBUG = True
        ENVIRONMENT = "development"
        LOGS_DIR = Path("logs")
        BACKEND_DATA_DIR = Path("backend_data")
        KARRAY_DATA_DIR = Path("karray_rag/data")
        OLLAMA_HOST = "localhost"
        OLLAMA_PORT = 11434
        QDRANT_HOST = "localhost"
        QDRANT_PORT = 6333

        def _get_env(self, key, default):
            return os.getenv(key, default)

        def _get_int_env(self, key, default):
            try:
                return int(os.getenv(key, str(default)))
            except ValueError:
                return default

        def validate_configuration(self):
            return []

        def is_production(self):
            return False

    config = MockConfig()

from api_server import app
import uvicorn

def setup_environment():
    """Setup environment and check dependencies."""
    logger.info("Setting up K-Array Chat API environment...")

    # Check required directories
    required_dirs = [
        config.LOGS_DIR,
        config.BACKEND_DATA_DIR,
        config.KARRAY_DATA_DIR
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.info(f"Creating directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

    # Check configuration
    config_errors = config.validate_configuration()
    if config_errors:
        logger.warning("Configuration validation issues found:")
        for error in config_errors:
            logger.warning(f"  - {error}")

        if config.is_production():
            logger.error("Cannot start in production with configuration errors")
            sys.exit(1)

    logger.info("Environment setup complete")

def main():
    """Main entry point."""
    try:
        setup_environment()

        # Configuration
        host = config._get_env("KCHAT_API_HOST", "0.0.0.0")
        port = config._get_int_env("KCHAT_API_PORT", 8000)
        debug = config.DEBUG
        reload = debug and not config.is_production()

        logger.info("=" * 60)
        logger.info("\U0001F680 Starting K-Array Chat API Server")
        logger.info("=" * 60)
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Debug: {debug}")
        logger.info(f"Environment: {config.ENVIRONMENT}")
        logger.info(f"Ollama: {config.OLLAMA_HOST}:{config.OLLAMA_PORT}")
        logger.info(f"Qdrant: {config.QDRANT_HOST}:{config.QDRANT_PORT}")
        logger.info("=" * 60)

        # Handle asyncio loop exceptions globally
        def handle_asyncio_exception(loop, context):
            logger.error(f"Unhandled asyncio exception: {context}")
        asyncio.get_event_loop().set_exception_handler(handle_asyncio_exception)

        # Start server
        uvicorn.run(
            "api_server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info" if debug else "warning",
            access_log=debug
        )

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
