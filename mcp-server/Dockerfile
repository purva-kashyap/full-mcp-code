# Multi-stage build for MCP Server
FROM python:3.12-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create directory for token cache
RUN mkdir -p /app/cache && chmod 755 /app/cache

# Expose ports
# 8000 - FastAPI (OAuth callbacks)
# 8001 - MCP server
EXPOSE 8000 8001

# Health check on FastAPI endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the server
CMD ["python", "main.py"]
