# Multi-stage Dockerfile for Kchat application
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov ruff mypy black

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "main.py"]

# Production stage
FROM base as production

# Copy only necessary application files
COPY agents/ ./agents/
COPY config/ ./config/
COPY docs/ ./docs/
COPY knowledge_pipeline/ ./knowledge_pipeline/
COPY karray_rag/ ./karray_rag/
COPY models/ ./models/
COPY utils/ ./utils/
COPY main.py .
COPY prompts.py .
COPY intent_router.py .
COPY language_detector.py .
COPY translator.py .
COPY verifier.py .
COPY openchat_worker.py .
COPY clarification_prompt.py .
COPY knowledge_pipeline.py .

# Create necessary directories
RUN mkdir -p logs quotes backend_data embeddings

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from agents.context import AgentContext; print('OK')" || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["python", "main.py"]

# Testing stage
FROM development as testing

# Run tests
RUN python -m pytest tests/ -v --tb=short

# Lint and type checking
RUN ruff check .
RUN mypy . --ignore-missing-imports