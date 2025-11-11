#!/usr/bin/env python3
"""
OAuth Callback Server
Separate service to handle OAuth callbacks from Microsoft
Can be deployed independently in Kubernetes
"""
import os
import sys
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import time

# Store callback data with timestamp
# In production, replace this with Redis or a database
_callback_store = {}
_callback_lock = threading.Lock()

# Cleanup old callbacks after 10 minutes
CALLBACK_EXPIRY = 600


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture and store OAuth callbacks"""
    
    def do_GET(self):
        """Handle GET request from OAuth redirect"""
        
        # Parse the callback URL
        parsed = urlparse(self.path)
        
        if parsed.path == '/callback':
            self._handle_oauth_callback(parsed)
        elif parsed.path == '/health':
            self._handle_health_check()
        elif parsed.path.startswith('/api/callback/'):
            self._handle_callback_retrieval(parsed)
        else:
            self._send_404()
    
    def _handle_oauth_callback(self, parsed):
        """Handle OAuth callback from Microsoft"""
        params = parse_qs(parsed.query)
        
        auth_code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        error = params.get('error', [None])[0]
        error_description = params.get('error_description', [None])[0]
        
        # Store the callback data
        with _callback_lock:
            _callback_store[state] = {
                'auth_code': auth_code,
                'state': state,
                'error': error,
                'error_description': error_description,
                'timestamp': time.time(),
                'retrieved': False
            }
        
        # Clean up old callbacks
        self._cleanup_old_callbacks()
        
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
                <p><strong>Error:</strong> {error}</p>
                {f'<p><strong>Description:</strong> {error_description}</p>' if error_description else ''}
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
                <p style="color: #666; font-size: 0.9em; margin-top: 30px;">
                    Your authentication code has been securely stored and will be retrieved by the application.
                </p>
            </body>
            </html>
            """
        self.wfile.write(html.encode())
        
        print(f"[{datetime.now().isoformat()}] OAuth callback received for state: {state}", file=sys.stderr)
    
    def _handle_health_check(self):
        """Health check endpoint for Kubernetes"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'service': 'oauth-callback-server',
            'timestamp': datetime.now().isoformat(),
            'active_callbacks': len(_callback_store)
        }
        self.wfile.write(json.dumps(response).encode())
    
    def _handle_callback_retrieval(self, parsed):
        """API endpoint to retrieve callback data"""
        # Extract state from path: /api/callback/{state}
        state = parsed.path.split('/')[-1]
        
        with _callback_lock:
            callback_data = _callback_store.get(state)
            
            if callback_data and not callback_data['retrieved']:
                # Mark as retrieved
                callback_data['retrieved'] = True
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')  # For CORS
                self.end_headers()
                
                response = {
                    'status': 'success',
                    'auth_code': callback_data['auth_code'],
                    'state': callback_data['state'],
                    'error': callback_data['error'],
                    'error_description': callback_data['error_description']
                }
                self.wfile.write(json.dumps(response).encode())
                
                print(f"[{datetime.now().isoformat()}] Callback data retrieved for state: {state}", file=sys.stderr)
            elif callback_data and callback_data['retrieved']:
                self._send_error(410, 'Callback already retrieved')
            else:
                self._send_error(404, 'Callback not found or expired')
    
    def _cleanup_old_callbacks(self):
        """Remove callbacks older than CALLBACK_EXPIRY seconds"""
        current_time = time.time()
        with _callback_lock:
            expired_states = [
                state for state, data in _callback_store.items()
                if current_time - data['timestamp'] > CALLBACK_EXPIRY
            ]
            for state in expired_states:
                del _callback_store[state]
                print(f"[{datetime.now().isoformat()}] Cleaned up expired callback for state: {state}", file=sys.stderr)
    
    def _send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <html>
        <head><title>Not Found</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>404 - Not Found</h1>
            <p>Available endpoints:</p>
            <ul style="list-style: none;">
                <li>/callback - OAuth callback endpoint</li>
                <li>/health - Health check</li>
                <li>/api/callback/{state} - Retrieve callback data</li>
            </ul>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def _send_error(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {'status': 'error', 'message': message}
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Log messages to stderr"""
        print(f"[{datetime.now().isoformat()}] {format % args}", file=sys.stderr)


def run_callback_server():
    """Start the OAuth callback server"""
    host = os.getenv('OAUTH_CALLBACK_HOST', '0.0.0.0')
    port = int(os.getenv('OAUTH_CALLBACK_PORT', '8000'))
    
    try:
        server = HTTPServer((host, port), OAuthCallbackHandler)
        
        print(f"", file=sys.stderr)
        print(f"🚀 OAuth Callback Server", file=sys.stderr)
        print(f"=" * 50, file=sys.stderr)
        print(f"✅ Server started on http://{host}:{port}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"📍 Endpoints:", file=sys.stderr)
        print(f"   - OAuth Callback: http://{host}:{port}/callback", file=sys.stderr)
        print(f"   - Health Check:   http://{host}:{port}/health", file=sys.stderr)
        print(f"   - API:            http://{host}:{port}/api/callback/{{state}}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"⏰ Callback expiry: {CALLBACK_EXPIRY} seconds", file=sys.stderr)
        print(f"=" * 50, file=sys.stderr)
        print(f"", file=sys.stderr)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print(f"\n\n🛑 Server stopped by user", file=sys.stderr)
        server.shutdown()
    except Exception as e:
        print(f"\n❌ Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_callback_server()
