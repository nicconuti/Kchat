# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based retrieval and web scraping system designed to extract technical specifications and content from K-Array's website. The project implements a sophisticated data extraction pipeline with emphasis on zero-hallucination quality and source attribution.

## Common Commands

### Setup and Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install and start Milvus vector database (required for chat system)
# Option 1: Docker (recommended)
docker run -d --name milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest

# Option 2: Local installation
# Follow: https://milvus.io/docs/install_standalone-docker.md

# Create necessary directories (done automatically by the system)
mkdir -p data/extracted_content data/verified_specs data/quality_reports data/extraction_logs
```

### Running Extraction Scripts
```bash
# Run the main extraction orchestrator (MVP quality focus)
python src/extraction_orchestrator.py

# Run systematic scraper (processes ALL URLs from sitemap.xml)
python src/systematic_scraper.py

# Generate complete todo list
python generate_complete_todolist.py

# Download PDFs from sitemap
python download_pdfs.py
```

### Running the Chat System
```bash
# First-time setup (initialize vector store and check configuration)
python setup_chat.py

# Launch the chat interface
python k_array_chat.py

# The chat will be available at: http://localhost:7860
```

### Development Commands
```bash
# Run Python scripts with proper module path
python -m src.extraction_orchestrator
python -m src.systematic_scraper

# Check Python syntax
python -m py_compile src/*.py
```

## Architecture Overview

### Core Components

1. **Web Scraping & Extraction Pipeline**
   - `src/extraction_orchestrator.py`: Main orchestrator with MVP quality focus, implements tier-based processing
   - `src/systematic_scraper.py`: Comprehensive scraper that processes ALL URLs from sitemap.xml

2. **Vector Store & Retrieval System**
   - `src/enhanced_vector_store.py`: Advanced Milvus-based vector store with hybrid search capabilities
   - `src/smart_retriever.py`: Intelligent retrieval with context awareness and query analysis
   - `src/multi_vector_retriever.py`: Multi-strategy retrieval system for maximum quality

3. **Chat System Components**
   - `src/response_engine.py`: Zero-hallucination response generation with dual LLM fallback
   - `src/reranker.py`: Quality-based result reranking and relevance scoring
   - `src/query_intelligence.py`: Advanced query analysis and optimization
   - `k_array_chat.py`: Main Gradio chat interface with session memory

4. **Configuration & Utilities**
   - `src/llm_manager.py`: Multi-provider LLM management (Gemini/OpenAI)
   - `src/config.py`: Centralized configuration with environment variable support
   - `src/dynamic_config.py`: Runtime configuration management
   - `setup_chat.py`: Automated setup script for chat system initialization

### Key Design Patterns

- **Zero-Hallucination System**: All components implement strict source attribution and explicit value extraction
- **Tier-Based Processing**: URLs are prioritized (Tier 1: Product specs, Tier 2: Applications, Tier 3: General)
- **Multi-Vector Retrieval**: Combines semantic, keyword, and hybrid search strategies
- **Quality Validation**: Multi-layer quality checks with confidence scoring and result reranking
- **Progressive Enhancement**: Starts with individual products, then applications, then case studies

### Data Flow

1. **Sitemap Processing**: Load and categorize all URLs from `sitemap.xml`
2. **Prioritized Extraction**: Process URLs in batches based on content type
3. **Quality Validation**: Apply MVP-quality standards with source attribution
4. **Cross-Verification**: Compare specifications across multiple sources
5. **Dataset Generation**: Create final verified dataset with quality metrics

## Configuration

### Environment Variables
Set these in a `.env` file or environment:
- `GEMINI_API_KEY`: For Gemini AI access
- `OPENAI_API_KEY`: For OpenAI access  
- `DEFAULT_LLM_PROVIDER`: "gemini" or "openai"
- `VECTOR_STORE_DIRECTORY`: Vector store data path (default: "./data/vector_store")
- `MILVUS_HOST`: Milvus server host (default: "localhost")
- `MILVUS_PORT`: Milvus server port (default: 19530)

### Key Configuration Options
- **Extraction Strategy**: MVP focus vs. complete sitemap processing
- **Quality Thresholds**: Confidence scores, validation rules
- **Batch Processing**: URLs per batch, delays between requests
- **Output Formats**: JSON with full traceability

## Data Storage

### Directory Structure
- `data/`: Main data directory
  - `extracted_data_*.json`: Individual extraction results (numbered 001-231+)
  - `vector_store/`: Milvus vector store data
  - `extraction_logs/`: Detailed processing logs
  - `quality_reports/`: Quality metrics and validation results

### Data Files
- `sitemap.xml`: Source of all URLs to process
- `todolist_progress.json`: Processing progress tracking
- `requirements.txt`: Python dependencies

## Quality Standards

### MVP Requirements
- **Source Attribution**: Every technical fact must include exact source quote
- **No Speculation**: Use "Not specified" instead of estimating values
- **Cross-Verification**: Multiple sources validated for consistency  
- **Confidence Scoring**: 80%+ minimum for production use
- **Traceability**: Full extraction history and timestamps

### Extraction Strategies
- **Product Specs**: Focus on technical specifications with exact values
- **Application Guides**: Extract explicit recommendations and challenges
- **Case Studies**: Document real implementations with specific products
- **PDF Processing**: Extract from datasheets for cross-verification

## Important Implementation Notes

- The system uses WebFetch tools for actual content extraction
- All extraction prompts emphasize zero-hallucination requirements
- Quality validation includes multiple checks for speculation words
- Progress tracking enables resumable operations
- Milvus provides high-performance vector similarity search with hybrid capabilities
- Multiple LLM providers supported with failover capability
- Advanced query intelligence with multi-strategy retrieval