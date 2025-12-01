"""Main entry point for Application MCP Server"""
import asyncio
import uvicorn
from src.application_mcp.server import app as fastapi_app
from src.application_mcp.mcp_instance import mcp
# Import tools to register them
from src.application_mcp import tools  # noqa: F401


async def run_server():
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
    print("🚀 Starting Microsoft 365 Application MCP Server...")
    print("   - FastAPI: http://localhost:8000")
    print("   - MCP endpoint: http://localhost:8001/mcp")
    print("   - Health check: http://localhost:8000/health")
    print()
    print("📝 Architecture:")
    print("   - Authentication: Client Credentials Flow (no user login)")
    print("   - Permissions: Application permissions (app acts on its own behalf)")
    print("   - Token caching: In-memory (single app token)")
    print("   - Access: Can read any user's mailbox in the organization")
    print()
    print("⚠️  Requirements:")
    print("   - Application permissions configured in Azure Portal")
    print("   - Admin consent granted for Mail.Read permission")
    print("   - AZURE_TENANT_ID must be your organization's tenant ID")
    print()
    
    asyncio.run(run_server())
