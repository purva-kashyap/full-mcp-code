"""FastAPI server for health checks and metrics endpoints"""
from datetime import datetime
from fastapi import FastAPI, HTTPException
from .config import config
from .metrics import metrics_collector
from .logging_config import get_logger
from .rate_limiter import get_limiter_stats
from . import auth, graph

logger = get_logger(__name__)

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
        "endpoints": {
            "mcp": "http://localhost:8001/mcp (or K8s service)",
            "health": "/health",
            "health_detailed": "/health/detailed",
            "metrics": "/metrics",
        }
    }


@app.get("/health")
async def health():
    """
    Basic health check endpoint.
    
    Returns 200 if service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/health/detailed")
async def health_detailed():
    """
    Detailed health check including Azure AD and Graph API connectivity.
    
    Returns:
        Detailed health status including token acquisition and API connectivity
    """
    checks = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "healthy",
        "checks": {}
    }
    
    # Check 1: Token acquisition
    try:
        token = auth.get_token()
        checks["checks"]["token_acquisition"] = {
            "status": "healthy",
            "message": "Successfully acquired token",
            "token_length": len(token)
        }
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["checks"]["token_acquisition"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        logger.error("Health check failed: token acquisition", exc_info=True)
    
    # Check 2: HTTP client
    try:
        client = await graph.get_http_client()
        checks["checks"]["http_client"] = {
            "status": "healthy",
            "message": "HTTP client initialized",
            "is_closed": client.is_closed
        }
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["checks"]["http_client"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        logger.error("Health check failed: HTTP client", exc_info=True)
    
    # Check 3: Configuration validation
    config_errors = config.validate()
    if config_errors:
        checks["status"] = "unhealthy"
        checks["checks"]["configuration"] = {
            "status": "unhealthy",
            "errors": config_errors
        }
    else:
        checks["checks"]["configuration"] = {
            "status": "healthy",
            "message": "All required configuration present"
        }
    
    # Return 503 if unhealthy
    if checks["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=checks)
    
    return checks


@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for monitoring and observability.
    
    Returns:
        Global and per-endpoint metrics, including rate limiter status
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "global": metrics_collector.get_global_metrics(),
        "endpoints": metrics_collector.get_endpoint_metrics(),
        "rate_limiters": get_limiter_stats(),
    }

