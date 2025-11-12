"""Main entry point for Hybrid MCP Server"""
import asyncio
import uvicorn
from src.hybrid_mcp.server import app as fastapi_app
from src.hybrid_mcp.mcp_instance import mcp
# Import tools to register them
from src.hybrid_mcp import tools  # noqa: F401


async def run_hybrid_server():
    """Run both FastAPI and FastMCP concurrently"""
    print("✅ Running FastAPI (port 8000) and MCP (port 8001) concurrently")
    
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
    print("🚀 Starting Microsoft 365 Hybrid MCP Server...")
    print("   - FastAPI: http://localhost:8000")
    print("   - OAuth callbacks: http://localhost:8000/callback")
    print("   - MCP endpoint: http://localhost:8001/mcp")
    print("   - Health check: http://localhost:8000/health")
    print()
    print("📝 Architecture:")
    print("   - Token caching with MSAL SerializableTokenCache")
    print("   - acquire_token_silent for automatic token refresh")
    print("   - Separate modules: auth.py, graph.py, tools.py, server.py")
    print("   - Similar structure to microsoft-mcp")
    print()
    
    asyncio.run(run_hybrid_server())
