#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║     Complete Demo: AI Agent + Mock MCP Server             ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python --version)${NC}"

# Check pip
if ! command -v pip &> /dev/null; then
    echo -e "${RED}❌ pip is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip found${NC}"

echo ""
echo -e "${YELLOW}📋 What this demo will do:${NC}"
echo "  1. Start the mock MCP server (no Azure credentials needed)"
echo "  2. Run automated tests to verify it's working"
echo "  3. Show you how to use the AI agent"
echo ""

read -p "Press Enter to continue..."

# Change to application-mcp-server directory
cd "$(dirname "$0")/application-mcp-server" || exit 1

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 1: Installing dependencies...${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Check if dependencies are installed
if python -c "import fastmcp" 2>/dev/null; then
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
else
    echo -e "${YELLOW}📦 Installing MCP server dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ MCP server dependencies installed${NC}"
fi

# Check AI agent dependencies
cd ../ai-agent || exit 1
if python -c "import openai" 2>/dev/null || python -c "import anthropic" 2>/dev/null; then
    echo -e "${GREEN}✅ AI agent dependencies already installed${NC}"
else
    echo -e "${YELLOW}📦 Installing AI agent dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ AI agent dependencies installed${NC}"
fi

cd ../application-mcp-server || exit 1

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 2: Starting Mock MCP Server...${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}⚠️  The server will start in the background.${NC}"
echo -e "${YELLOW}   Press Ctrl+C when you're done testing to stop it.${NC}"
echo ""

# Start the mock server in the background
python main_mock.py &
SERVER_PID=$!

# Wait for server to start
echo -e "${YELLOW}⏳ Waiting for server to start...${NC}"
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✅ Mock MCP Server is running (PID: $SERVER_PID)${NC}"
    echo -e "${GREEN}   - FastAPI: http://localhost:8000${NC}"
    echo -e "${GREEN}   - MCP endpoint: http://localhost:8001/mcp${NC}"
else
    echo -e "${RED}❌ Failed to start server${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 3: Running Tests...${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Wait a bit more to ensure server is ready
sleep 2

# Run tests
python test_mock.py

TEST_RESULT=$?

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 4: Next Steps - Using the AI Agent${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo -e "${YELLOW}The mock MCP server is running and ready!${NC}"
    echo ""
    echo -e "To use the AI agent:"
    echo ""
    echo -e "  1. ${BLUE}In a NEW terminal${NC}, run:"
    echo -e "     ${GREEN}cd ai-agent${NC}"
    echo -e "     ${GREEN}cp .env.example .env${NC}"
    echo -e "     ${GREEN}nano .env  # Add your OPENAI_API_KEY or ANTHROPIC_API_KEY${NC}"
    echo -e "     ${GREEN}python agent.py${NC}"
    echo ""
    echo -e "  2. Then ask questions like:"
    echo -e "     ${BLUE}• List all users in the organization${NC}"
    echo -e "     ${BLUE}• Show me recent emails from john.doe@company.com${NC}"
    echo -e "     ${BLUE}• What teams exist?${NC}"
    echo -e "     ${BLUE}• Who are the members of the Engineering team?${NC}"
    echo ""
    echo -e "${YELLOW}📚 Documentation:${NC}"
    echo -e "   • Quick Start: ${BLUE}QUICKSTART.md${NC}"
    echo -e "   • Architecture: ${BLUE}ARCHITECTURE.md${NC}"
    echo -e "   • Mock Server Guide: ${BLUE}application-mcp-server/MOCK_SERVER.md${NC}"
    echo ""
else
    echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"
    echo ""
fi

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the mock server and exit${NC}"
echo ""

# Keep the script running so server stays alive
wait $SERVER_PID
