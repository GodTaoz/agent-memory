# Dockerfile for Memory MCP Server
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY config/ ./config/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[mcp]"

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5678

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5678/api/v1/health')" || exit 1

# Run the server
CMD ["uvicorn", "memory_mcp.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "5678"]
