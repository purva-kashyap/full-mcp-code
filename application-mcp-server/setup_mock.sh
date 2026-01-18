#!/bin/bash

echo "🚀 Setting up Mock MCP Server + AI Agent"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "main_mock.py" ]; then
    echo "❌ Error: Please run this script from the application-mcp-server directory"
    exit 1
fi

echo "📦 Step 1: Installing application-mcp-server dependencies..."
pip install -r requirements.txt

echo ""
echo "📦 Step 2: Installing ai-agent dependencies..."
cd ../ai-agent
pip install -r requirements.txt

echo ""
echo "⚙️  Step 3: Setting up ai-agent environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit ai-agent/.env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY"
else
    echo "ℹ️  .env file already exists"
fi

cd ../application-mcp-server

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit ai-agent/.env and add your LLM API key:"
echo "   nano ../ai-agent/.env"
echo ""
echo "2. Start the mock MCP server (in this terminal):"
echo "   python main_mock.py"
echo ""
echo "3. Test the mock server (in another terminal):"
echo "   python test_mock.py"
echo ""
echo "4. Run the AI agent (in another terminal):"
echo "   cd ../ai-agent && python agent.py"
echo ""
echo "=========================================="
