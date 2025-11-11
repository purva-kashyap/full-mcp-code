#!/bin/bash

# Build and test OAuth Callback Server locally

echo "🏗️  Building OAuth Callback Server..."

# Build Docker image
docker build -t oauth-callback-server:latest .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "To run:"
    echo "  docker run -p 8000:8000 oauth-callback-server:latest"
    echo ""
    echo "Or run directly:"
    echo "  python3 oauth_callback_server.py"
else
    echo "❌ Build failed"
    exit 1
fi
