import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .mcp_instance import mcp
# Import tools to register them with the mcp instance
from . import tools  # noqa: F401

# Global variable to store the callback data
_callback_data = {"url": None, "ready": threading.Event(), "auth_code": None, "state": None, "error": None}


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture the OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from OAuth redirect"""
        global _callback_data
        
        # Parse the callback URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        auth_code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        error = params.get('error', [None])[0]
        
        # Store the callback data
        _callback_data["url"] = self.path
        _callback_data["auth_code"] = auth_code
        _callback_data["state"] = state
        _callback_data["error"] = error
        
        # Send response to browser
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if error:
            html = f"""
            <html>
            <head><title>Authentication Failed</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>You can close this window and try again.</p>
            </body>
            </html>
            """
        else:
            html = """
            <html>
            <head><title>Authentication Successful</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>✅ Authentication Successful!</h1>
                <p>You can close this window and return to your application.</p>
            </body>
            </html>
            """
        self.wfile.write(html.encode())
        
        # Signal that we got the callback
        _callback_data["ready"].set()
    
    def log_message(self, format, *args):
        """Suppress server log messages"""
        pass


def start_oauth_callback_server():
    """Start HTTP server to listen for OAuth callback on port 8000
    
    This is optional - only starts if MICROSOFT_MCP_ENABLE_CALLBACK_SERVER=true
    In Kubernetes, use a separate oauth_callback_server.py deployment instead
    """
    # Check if callback server should be enabled
    enable_callback = os.getenv("MICROSOFT_MCP_ENABLE_CALLBACK_SERVER", "true").lower() == "true"
    
    if not enable_callback:
        print(f"ℹ️  Built-in OAuth callback server disabled", file=sys.stderr)
        print(f"   Using external callback service at: {os.getenv('MICROSOFT_MCP_REDIRECT_URI', 'http://localhost:8000/callback')}", file=sys.stderr)
        return None
    
    callback_port = int(os.getenv("OAUTH_CALLBACK_PORT", "8000"))
    
    try:
        server = HTTPServer(('localhost', callback_port), OAuthCallbackHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"✅ OAuth callback server started on http://localhost:{callback_port}", file=sys.stderr)
        return server
    except OSError as e:
        print(f"⚠️  Warning: Could not start OAuth callback server on port {callback_port}: {e}", file=sys.stderr)
        print(f"   You may need to use an external callback service", file=sys.stderr)
        return None


def run_server() -> None:
    """Start the MCP server with OAuth callback support"""
    client_id = os.getenv("MICROSOFT_MCP_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_MCP_CLIENT_SECRET")
    
    if not client_id:
        print(
            "Error: MICROSOFT_MCP_CLIENT_ID environment variable is required",
            file=sys.stderr,
        )
        sys.exit(1)
    
    print(f"✅ Client ID: {client_id}", file=sys.stderr)
    if client_secret:
        print(f"✅ Client Secret: {client_secret[:10]}... (SET)", file=sys.stderr)
    else:
        print(f"⚠️  Client Secret: NOT SET (will use public client mode)", file=sys.stderr)

    # Start OAuth callback server on port 8000 (optional, controlled by env var)
    start_oauth_callback_server()

    # Run with streamable HTTP transport
    # Default host is 0.0.0.0 and port is 8001 (8000 is reserved for OAuth callback)
    # You can override with HOST and PORT environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    print(f"\n🚀 Starting Microsoft MCP server with streamable-http transport on {host}:{port}", file=sys.stderr)
    print(f"   Server will be available at: http://{host}:{port}/mcp/", file=sys.stderr)
    print("", file=sys.stderr)
    
    mcp.run(transport="streamable-http", host=host, port=port)
