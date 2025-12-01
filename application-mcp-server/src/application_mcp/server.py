"""FastAPI server for health checks (no OAuth callbacks needed for app permissions)"""
from datetime import datetime
from fastapi import FastAPI

app = FastAPI(title="Application MCP Server")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Microsoft 365 Application MCP Server",
        "version": "1.0.0",
        "auth_type": "client_credentials",
        "permissions_type": "application",
        "description": "MCP server using Application permissions - no user interaction required",
        "mcp_endpoint": "http://localhost:8001/mcp (or K8s service)",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
