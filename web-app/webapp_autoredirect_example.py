"""
Alternative webapp.py with auto-redirect for unauthenticated users
No "Sign in" button - automatically starts OAuth when not authenticated
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import asyncio
import json
from fastmcp import Client
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

MCP_SERVER_URL = "http://0.0.0.0:8001/mcp/"


async def call_mcp_server(tool_name: str, params: dict):
    """Helper to call MCP server tools"""
    async with Client(MCP_SERVER_URL) as client:
        result = await client.call_tool(tool_name, params)
        if result.content and len(result.content) > 0:
            return json.loads(result.content[0].text)
        return None


@app.route('/')
def index():
    """Home page - check if user is authenticated"""
    account_id = session.get('account_id')
    username = session.get('username')
    
    if account_id and username:
        return render_template('dashboard.html', username=username)
    
    # Instead of showing login button, redirect to start auth
    return redirect(url_for('auto_start_auth'))


@app.route('/auto-login')
def auto_start_auth():
    """Automatically start OAuth flow and redirect to Microsoft"""
    try:
        # Call MCP server to get auth URL
        auth_data = asyncio.run(call_mcp_server('authenticate_account', {}))
        
        # Store state in session for later verification
        session['oauth_state'] = auth_data['state']
        session['auth_started'] = True
        
        # Redirect browser directly to Microsoft login
        return redirect(auth_data['auth_url'])
        
    except Exception as e:
        return f"Error starting authentication: {str(e)}", 500


@app.route('/callback')
def oauth_callback():
    """Handle OAuth callback from Microsoft"""
    # Note: This won't work with the current setup because 
    # Microsoft redirects to callback-server:8000/callback
    # This is just to show the concept
    code = request.args.get('code')
    state = request.args.get('state')
    
    if state != session.get('oauth_state'):
        return "Invalid state", 400
    
    try:
        # Complete authentication
        complete_data = asyncio.run(call_mcp_server('complete_authentication', {
            'auth_code': code,
            'state': state
        }))
        
        if complete_data.get('status') == 'success':
            session['account_id'] = complete_data['account_id']
            session['username'] = complete_data['username']
            return redirect(url_for('index'))
        
        return "Authentication failed", 400
        
    except Exception as e:
        return f"Error: {str(e)}", 500


# ... rest of the endpoints remain the same ...


if __name__ == '__main__':
    app.run(debug=True, port=5000)
