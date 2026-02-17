"""FastAPI server for health checks and metrics endpoints"""
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from .config import config
from .metrics import metrics_collector
from .logging_config import get_logger
from .rate_limiter import get_limiter_stats
from . import auth, graph
from .exceptions import (
    MCPServerError,
    AuthenticationError,
    GraphAPIError,
    RateLimitError,
    NetworkError,
    ConfigurationError,
    ValidationError,
)

logger = get_logger(__name__)

app = FastAPI(title="Application MCP Server")


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "error": exc.message,
            "details": exc.details
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """Handle configuration errors"""
    logger.error(
        "Configuration error",
        extra={
            "path": request.url.path,
            "error": exc.message,
            "details": exc.details
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    logger.error(
        "Authentication error",
        extra={
            "path": request.url.path,
            "error": exc.message,
            "details": exc.details
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    """Handle rate limit errors with retry-after header"""
    logger.warning(
        "Rate limit exceeded",
        extra={
            "path": request.url.path,
            "error": exc.message,
            "retry_after": exc.retry_after
        }
    )
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=headers
    )


@app.exception_handler(NetworkError)
async def network_error_handler(request: Request, exc: NetworkError):
    """Handle network errors"""
    logger.error(
        "Network error",
        extra={
            "path": request.url.path,
            "error": exc.message,
            "details": exc.details
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(GraphAPIError)
async def graph_api_error_handler(request: Request, exc: GraphAPIError):
    """Handle Microsoft Graph API errors"""
    logger.error(
        "Graph API error",
        extra={
            "path": request.url.path,
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(MCPServerError)
async def mcp_server_error_handler(request: Request, exc: MCPServerError):
    """Handle all other MCP server errors"""
    logger.error(
        "MCP server error",
        extra={
            "path": request.url.path,
            "error": exc.message,
            "details": exc.details
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


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

