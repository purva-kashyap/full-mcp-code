"""
Hybrid FastAPI + FastMCP Server
Combines OAuth callback handling with MCP server in a single application
"""
import os
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastmcp import FastMCP
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# OAuth Callback Storage (In-Memory)
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

def get_callback(state: str) -> Optional[dict]:
    """Retrieve and mark OAuth callback data as retrieved"""
    with _callback_lock:
        if state in _callback_store:
            data = _callback_store[state]
            # Check if expired
            if datetime.now() - data["timestamp"] > timedelta(seconds=CALLBACK_EXPIRY):
                del _callback_store[state]
                return None
            # Mark as retrieved
            data["retrieved"] = True
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
# FastMCP Server Setup
# ============================================================================
mcp = FastMCP("microsoft-365-hybrid-mcp-server")

@mcp.tool
async def authenticate_user() -> dict:
    """
    Complete OAuth authentication flow automatically.
    Opens browser, waits for callback, and returns access token.
    
    Returns:
        Dictionary with access_token and user info, or error
    """
    import secrets
    import webbrowser
    from urllib.parse import urlencode
    
    # Generate state
    state = secrets.token_urlsafe(32)
    
    # Microsoft OAuth parameters
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant = os.getenv("AZURE_TENANT_ID", "consumers")
    scopes = "User.Read Mail.Read offline_access"
    callback_url = "http://localhost:8000/callback"
    
    # Build authorization URL
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": callback_url,
        "response_mode": "query",
        "scope": scopes,
        "state": state,
    }
    
    auth_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{urlencode(params)}"
    
    # Open browser automatically
    webbrowser.open(auth_url)
    
    # Wait for callback (60 seconds timeout)
    import time
    start_time = time.time()
    timeout = 60
    
    while time.time() - start_time < timeout:
        callback_data = get_callback(state)
        
        if callback_data:
            # Check for errors
            if callback_data.get("error"):
                return {
                    "success": False,
                    "error": callback_data["error"],
                    "error_description": callback_data.get("error_description", "")
                }
            
            # Exchange code for token
            auth_code = callback_data["auth_code"]
            
            from msal import ConfidentialClientApplication
            
            app = ConfidentialClientApplication(
                client_id,
                authority=f"https://login.microsoftonline.com/{tenant}",
                client_credential=client_secret,
            )
            
            result = app.acquire_token_by_authorization_code(
                auth_code,
                scopes=["User.Read", "Mail.Read"],
                redirect_uri=callback_url
            )
            
            if "access_token" in result:
                return {
                    "success": True,
                    "access_token": result["access_token"],
                    "expires_in": result.get("expires_in"),
                    "token_type": result.get("token_type", "Bearer")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "error_description": result.get("error_description", "")
                }
        
        await asyncio.sleep(2)  # Poll every 2 seconds
    
    return {
        "success": False,
        "error": "timeout",
        "error_description": f"No callback received within {timeout} seconds"
    }

@mcp.tool
async def get_user_profile(access_token: str) -> dict:
    """
    Get user profile from Microsoft Graph.
    
    Args:
        access_token: OAuth access token
    
    Returns:
        User profile information
    """
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "message": response.text
            }

# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(title="Microsoft 365 Hybrid MCP Server")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Microsoft 365 Hybrid MCP Server",
        "mcp_endpoint": "/mcp (port 8001)",
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

# ============================================================================
# Run Server
# ============================================================================
async def run_hybrid_server():
    """Run both FastAPI and MCP server concurrently"""
    print("✅ Running FastAPI (port 8000) and MCP (port 8001) concurrently")
    
    async def run_fastapi():
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
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
    
    asyncio.run(run_hybrid_server())
