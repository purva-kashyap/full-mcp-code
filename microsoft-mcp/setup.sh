#!/bin/bash

# Setup script for Microsoft MCP Server

echo "🔧 Setting up Microsoft MCP Server..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    echo "   Please install Python 3.12 or later."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the server:"
echo "  1. Copy .env.example to .env and fill in your credentials"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run the server: python3 src/microsoft_mcp/server.py"
echo ""
echo "Or use the provided start script: ./start.sh"
