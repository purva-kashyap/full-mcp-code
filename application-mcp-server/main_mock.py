"""Main entry point for MOCK Application MCP Server (no MS credentials needed)"""
import asyncio
import uvicorn
import sys
import os

# Patch the import to use mock_graph instead of real graph
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Monkey patch the graph module before importing tools
from src.application_mcp import graph as real_graph
from src.application_mcp import mock_graph

# Replace all graph functions with mock versions
for attr_name in dir(mock_graph):
    if not attr_name.startswith('_'):
        setattr(real_graph, attr_name, getattr(mock_graph, attr_name))

# Now import the rest
from src.application_mcp.server import app as fastapi_app
from src.application_mcp.mcp_instance import mcp
from src.application_mcp import tools  # noqa: F401


async def run_server():
    """Run both FastAPI and FastMCP concurrently"""
    print("✅ Running MOCK FastAPI (port 8000) and MCP (port 8001) concurrently")
    print("⚠️  MOCK MODE: Using fake data, no Microsoft credentials required!")
    
    async def run_fastapi():
        config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    
    async def run_mcp():
        # Run MCP server with streamable HTTP transport
        await mcp.run_async(transport="http", host="0.0.0.0", port=8001, path="/mcp")
    
    # Run both servers concurrently
    await asyncio.gather(run_fastapi(), run_mcp())


if __name__ == "__main__":
    print("🚀 Starting MOCK Microsoft 365 Application MCP Server...")
    print("   - FastAPI: http://localhost:8000")
    print("   - MCP endpoint: http://localhost:8001/mcp")
    print("   - Health check: http://localhost:8000/health")
    print()
    print("⚠️  MOCK MODE ENABLED")
    print("   - No Azure credentials required")
    print("   - Returns realistic fake data")
    print("   - Perfect for testing and development")
    print()
    print("📝 Mock Data Includes:")
    print("   - 5 sample users (4 internal, 1 external guest)")
    print("   - Mock emails with various subjects and senders")
    print("   - 3 teams (Engineering, Product, Marketing)")
    print("   - Team channels and messages")
    print("   - Calendar events and online meetings")
    print()
    
    asyncio.run(run_server())
