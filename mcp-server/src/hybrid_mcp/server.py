"""FastAPI server for OAuth callbacks"""
import threading
from datetime import datetime, timedelta
from typing import Dict
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

# ============================================================================
# OAuth Callback Storage (In-Memory)
# For production K8s with multiple replicas, use Redis instead
# ============================================================================
_callback_store: Dict[str, dict] = {}
_callback_lock = threading.Lock()
CALLBACK_EXPIRY = 600  # 10 minutes


def store_callback(state: str, data: dict):
    """Store OAuth callback data"""
    with _callback_lock:
        _callback_store[state] = {
            **data,
            "timestamp": datetime.now(),
            "retrieved": False
        }


def get_callback(state: str):
    """Retrieve OAuth callback data"""
    with _callback_lock:
        if state in _callback_store:
            data = _callback_store[state]
            # Check if expired
            if datetime.now() - data["timestamp"] > timedelta(seconds=CALLBACK_EXPIRY):
                del _callback_store[state]
                return None
            return data
        return None


def cleanup_expired_callbacks():
    """Remove expired callbacks"""
    with _callback_lock:
        now = datetime.now()
        expired = [
            state for state, data in _callback_store.items()
            if now - data["timestamp"] > timedelta(seconds=CALLBACK_EXPIRY)
        ]
        for state in expired:
            del _callback_store[state]


# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(title="Hybrid MCP Server - OAuth Callbacks")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Microsoft 365 Hybrid MCP Server",
        "version": "1.0.0",
        "mcp_endpoint": "http://localhost:8001/mcp (or K8s service)",
        "oauth_callback": "/callback",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/callback")
async def oauth_callback(request: Request):
    """
    Handle OAuth redirect callback from Microsoft.
    Stores the authorization code or error for retrieval by MCP tools.
    """
    # Clean up expired callbacks periodically
    cleanup_expired_callbacks()
    
    params = dict(request.query_params)
    state = params.get("state")
    
    if not state:
        return HTMLResponse(
            content="<h1>Error: Missing state parameter</h1>",
            status_code=400
        )
    
    # Check for errors
    if "error" in params:
        store_callback(state, {
            "error": params["error"],
            "error_description": params.get("error_description", ""),
            "state": state
        })
        
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Authentication Error</title></head>
                <body style="font-family: Arial, sans-serif; padding: 50px; text-align: center;">
                    <h1 style="color: #d32f2f;">❌ Authentication Failed</h1>
                    <p><strong>Error:</strong> {params['error']}</p>
                    <p>{params.get('error_description', '')}</p>
                    <p style="margin-top: 30px; color: #666;">You can close this window.</p>
                </body>
            </html>
            """,
            status_code=400
        )
    
    # Success - store authorization code
    auth_code = params.get("code")
    if auth_code:
        store_callback(state, {
            "auth_code": auth_code,
            "state": state
        })
        
        return HTMLResponse(
            content="""
            <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial, sans-serif; padding: 50px; text-align: center;">
                    <h1 style="color: #4caf50;">✅ Authentication Successful!</h1>
                    <p>You have successfully authenticated with Microsoft 365.</p>
                    <p style="margin-top: 30px; color: #666;">You can close this window and return to your application.</p>
                    <script>
                        // Try to close the window (works if opened via window.open)
                        setTimeout(() => window.close(), 2000);
                    </script>
                </body>
            </html>
            """
        )
    
    return HTMLResponse(
        content="<h1>Error: Missing authorization code</h1>",
        status_code=400
    )


@app.get("/api/callback/{state}")
async def get_callback_status(state: str):
    """
    API endpoint to check if callback has been received for a given state.
    Used by clients to poll for callback completion.
    """
    callback_data = get_callback(state)
    
    if callback_data:
        return JSONResponse(content={
            "received": True,
            "data": {
                "auth_code": callback_data.get("auth_code"),
                "error": callback_data.get("error"),
                "error_description": callback_data.get("error_description")
            }
        })
    
    return JSONResponse(content={"received": False})
