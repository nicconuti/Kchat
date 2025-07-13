import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    """Configuration class for RAG application"""
    
    # LLM Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    
    # Vector Store Configuration
    VECTOR_STORE_DIRECTORY: str = os.getenv("VECTOR_STORE_DIRECTORY", "./data/vector_store")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Claude Scraper Configuration
    K_ARRAY_BASE_URL: str = "https://www.k-array.com"
    MAX_PDF_SIZE_MB: int = 15
    SCRAPING_BATCH_SIZE: int = 10
    
    # File Upload Configuration
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {'.pdf', '.csv', '.txt'}
    
    # RAG Configuration
    RETRIEVAL_TOP_K: int = 5
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        if cls.DEFAULT_LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when using Gemini provider")
        if cls.DEFAULT_LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        return True