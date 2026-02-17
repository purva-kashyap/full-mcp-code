"""Main entry point for Application MCP Server"""
import asyncio
import signal
import sys
import uvicorn
from src.application_mcp.server import app as fastapi_app
from src.application_mcp.mcp_instance import mcp
from src.application_mcp.config import config
from src.application_mcp.logging_config import setup_logging, get_logger
from src.application_mcp.graph import close_http_client
from src.application_mcp.metrics import metrics_collector
# Import tools to register them
from src.application_mcp import tools  # noqa: F401

logger = get_logger(__name__)

# Global flag for graceful shutdown
_shutdown_event = asyncio.Event()


async def run_server():
    """Run both FastAPI and FastMCP concurrently with graceful shutdown"""
    
    logger.info("Starting Microsoft 365 Application MCP Server")
    
    async def run_fastapi():
        config_obj = uvicorn.Config(
            fastapi_app,
            host=config.FASTAPI_HOST,
            port=config.FASTAPI_PORT,
            log_level="info"
        )
        server = uvicorn.Server(config_obj)
        
        # Wait for shutdown signal
        async def wait_for_shutdown():
            await _shutdown_event.wait()
            logger.info("FastAPI server shutting down...")
            server.should_exit = True
        
        shutdown_task = asyncio.create_task(wait_for_shutdown())
        
        try:
            await server.serve()
        finally:
            shutdown_task.cancel()
    
    async def run_mcp():
        # Run MCP server with streamable HTTP transport
        try:
            await mcp.run_async(
                transport="http",
                host=config.MCP_HOST,
                port=config.MCP_PORT,
                path="/mcp"
            )
        except asyncio.CancelledError:
            logger.info("MCP server shutting down...")
    
    async def log_periodic_metrics():
        """Log metrics summary every 5 minutes"""
        try:
            while not _shutdown_event.is_set():
                await asyncio.sleep(300)  # 5 minutes
                metrics_collector.log_metrics_summary()
        except asyncio.CancelledError:
            pass
    
    # Run both servers and metrics logger concurrently
    tasks = [
        asyncio.create_task(run_fastapi(), name="fastapi"),
        asyncio.create_task(run_mcp(), name="mcp"),
        asyncio.create_task(log_periodic_metrics(), name="metrics"),
    ]
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Server tasks cancelled")
    finally:
        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cleanup
        logger.info("Closing HTTP client...")
        await close_http_client()
        
        logger.info("Shutdown complete")


def handle_shutdown_signal(signum, frame):
    """Handle shutdown signals gracefully"""
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, initiating graceful shutdown...")
    _shutdown_event.set()


def main():
    """Main entry point with initialization and error handling"""
    
    # Setup logging first
    setup_logging()
    
    print("=" * 80)
    print("🚀 Microsoft 365 Application MCP Server")
    print("=" * 80)
    print()
    
    # Validate configuration
    logger.info("Validating configuration...")
    config_errors = config.validate()
    if config_errors:
        logger.error("Configuration validation failed:")
        for error in config_errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info("Configuration validated successfully")
    config.print_config()
    print()
    
    print("📡 Server Endpoints:")
    print(f"   - FastAPI: http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}")
    print(f"   - MCP endpoint: http://{config.MCP_HOST}:{config.MCP_PORT}/mcp")
    print(f"   - Health check: http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/health")
    print(f"   - Health (detailed): http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/health/detailed")
    print(f"   - Metrics: http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/metrics")
    print()
    
    print("📝 Architecture:")
    print("   - Authentication: Client Credentials Flow (no user login)")
    print("   - Permissions: Application permissions (app acts on its own behalf)")
    print("   - Token caching: Thread-safe in-memory (single app token)")
    print("   - Connection pooling: Enabled")
    print("   - Access: Can read any user's mailbox in the organization")
    print()
    
    print("⚠️  Requirements:")
    print("   - Application permissions configured in Azure Portal")
    print("   - Admin consent granted for required permissions")
    print("   - AZURE_TENANT_ID must be your organization's tenant ID")
    print()
    
    print("=" * 80)
    print()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    logger.info("Starting server tasks...")
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Server error", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
