#!/bin/bash

# Microsoft MCP Server Startup Script

echo "🚀 Starting Microsoft MCP Server..."

# Check if .env file exists and load it
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded environment from .env"
else
    echo "⚠️  No .env file found. Using environment variables..."
fi

# Check if environment variables are set
if [ -z "$MICROSOFT_MCP_CLIENT_ID" ]; then
    echo "❌ No .env file found and MICROSOFT_MCP_CLIENT_ID not set."
    echo "   Please copy .env.example to .env and fill in your credentials."
    exit 1
fi

echo "✅ Environment configured:"
echo "   MICROSOFT_MCP_CLIENT_ID=${MICROSOFT_MCP_CLIENT_ID}"
if [ -n "$MICROSOFT_MCP_CLIENT_SECRET" ]; then
    echo "   MICROSOFT_MCP_CLIENT_SECRET=${MICROSOFT_MCP_CLIENT_SECRET:0:10}..."
fi
echo ""

# Run the server
echo "🌐 Starting server..."
python3 main.py
