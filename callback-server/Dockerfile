# Dockerfile for OAuth Callback Server
FROM python:3.12-slim

WORKDIR /app

# Copy the callback server script (no dependencies needed - uses stdlib only)
COPY oauth_callback_server.py .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the callback server
CMD ["python3", "oauth_callback_server.py"]
