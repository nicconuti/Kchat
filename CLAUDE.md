# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Code Quality and Testing
```bash
# Linting and code style
ruff .

# Type checking
mypy .

# Run all tests
pytest

# Run tests with verbose output and capture logs
pytest -vv -s

# Run a specific test file
pytest tests/test_orchestrator_agent.py

# Run tests with coverage
pytest --cov
```

### Running the Application
```bash
# Interactive chat mode
python main.py

# Knowledge pipeline processing
python knowledge_pipeline.py path/to/documents --output knowledge_base.jsonl

# Run RAG pipeline with KArray data
python -c "from karray_rag import karray_rag_pipeline; karray_rag_pipeline.run_pipeline_with_karray()"
```

## High-Level Architecture

### Core Agent System
The system is built around a multi-agent architecture with shared memory through `AgentContext` (agents/context.py). All agents operate on the same context object, reading and writing different fields as they process user requests.

**Agent Orchestration Flow:**
1. `OrchestratorAgent` (agents/orchestrator_agent.py) coordinates the execution sequence
2. Uses LLM-based decision making via `choose_agent_sequence()` to determine which agents to run
3. Falls back to rule-based sequences if LLM orchestration fails
4. Each agent updates the shared context and logs its activity

**Key Agents:**
- `LanguageAgent` - Detects language, formality, and mixed-language input
- `IntentAgent` - Classifies user intent using both rule-based and LLM approaches
- `DocumentRetrieverAgent` - Retrieves relevant documents from Qdrant vector store
- `ResponseAgent` - Generates final responses using retrieved context or small talk
- `TranslationAgent` - Handles multilingual translation and auto-correction
- `VerificationAgent` - Validates response quality and relevance
- `ClarificationAgent` - Generates clarifying questions when intent is unclear

### Knowledge Pipeline System
The knowledge pipeline (knowledge_pipeline/) is a parallel document processing system that:

1. **File Processing**: Scans directories/ZIP files for supported document types
2. **Classification**: Uses dual-LLM classification with cross-checking for reliability
3. **Chunking**: Applies semantic chunking strategies based on document category
4. **Enrichment**: Generates summaries and hypothetical questions for each chunk
5. **Quality Control**: Quarantines files that fail processing or have low confidence scores

**Pipeline Components:**
- `FileScanner` - Discovers and validates input files
- `TextExtractor` - Extracts text from various document formats  
- `EntityExtractor` - Identifies entities within documents
- `AdvancedSemanticChunker` - Chunks text semantically
- `StructuredDataExtractor` - Handles structured data like product catalogs

### Logging and Monitoring
Each agent maintains dedicated log files in logs/ directory:
- `orchestration_trace.log` - Orchestration decisions and reasoning
- `pipeline_<pid>.log` - Knowledge pipeline processing logs
- Agent-specific logs for debugging individual components

### Local LLM Integration
Uses Ollama for local model serving:
- Primary model: `deepseek-r1:14b` for classification
- Fallback model: `mistral` for cross-checking and general tasks
- `openchat` for conversational responses

## Intent Categories

The system recognizes these primary intents:
- `technical_support_request` - Technical issues with products/services
- `product_information_request` - Product details and specifications  
- `cost_estimation` - Pricing and quote requests
- `booking_or_schedule` - Appointment scheduling
- `document_request` - Manual/documentation requests
- `open_ticket` - Explicit ticket creation requests
- `complaint` - Formal complaints
- `generic_smalltalk` - Casual conversation

## Key Configuration

- Document categories: `tech_assistance`, `software_assistance`, `product_price`, `product_guide`
- Supported file types: PDF, DOCX, TXT, CSV, various office formats
- Vector store: Qdrant for document retrieval
- Quarantine system for problematic files during pipeline processing

## Development Notes

- The codebase is primarily in Italian with Italian comments and logs
- All agents follow the pattern of receiving and returning `AgentContext`
- The system is designed to run completely offline without cloud dependencies
- Robust error handling with fallback mechanisms throughout the pipeline
- Comprehensive test suite covering all major components