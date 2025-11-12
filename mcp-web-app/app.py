"""Simple Flask web app for MCP Server integration"""
import os
import asyncio
from flask import Flask, render_template, session, redirect, url_for, request
from dotenv import load_dotenv
from mcp_client import MCPClient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")
CALLBACK_BASE_URL = os.getenv("CALLBACK_BASE_URL", "http://localhost:5000")

# Initialize MCP client
mcp = MCPClient(MCP_SERVER_URL)


@app.route('/')
async def index():
    """Home page - show login or user info"""
    # Check if user has an account in MCP server
    accounts = await mcp.list_accounts()
    
    if accounts:
        # User is logged in
        account = accounts[0]
        session['account_id'] = account['account_id']
        session['username'] = account['username']
        return render_template('index.html', 
                             logged_in=True, 
                             username=account['username'])
    else:
        # User not logged in
        session.clear()
        return render_template('index.html', logged_in=False)


@app.route('/login')
async def login():
    """Start OAuth authentication"""
    # Generate fresh auth URL for each login attempt
    result = await mcp.authenticate_account()
    
    # Store state and auth URL in session
    session['oauth_state'] = result['state']
    session['auth_url'] = result['auth_url']
    session.modified = True  # Force session save
    
    # Redirect to waiting page
    return redirect(url_for('auth_waiting'))


@app.route('/auth-waiting')
async def auth_waiting():
    """Waiting page that polls for authentication completion"""
    state = session.get('oauth_state')
    auth_url = session.get('auth_url')
    
    if not state or not auth_url:
        return redirect(url_for('index'))
    
    return render_template('auth_waiting.html')


@app.route('/check-auth')
async def check_auth():
    """API endpoint to check if authentication is complete"""
    state = session.get('oauth_state')
    if not state:
        return {"status": "error", "message": "No auth in progress"}
    
    # Check callback
    callback_result = await mcp.check_callback(state)
    
    if callback_result.get('received'):
        if callback_result.get('success'):
            # Complete authentication
            auth_code = callback_result['auth_code']
            account = await mcp.complete_authentication(auth_code)
            
            # Store in session
            session['account_id'] = account['account_id']
            session['username'] = account['username']
            session.pop('oauth_state', None)
            
            return {"status": "success", "redirect": url_for('index')}
        else:
            error = callback_result.get('error', 'Unknown error')
            session.pop('oauth_state', None)
            return {"status": "error", "message": error}
    
    return {"status": "waiting"}


@app.route('/emails')
async def emails():
    """List user's emails"""
    account_id = session.get('account_id')
    if not account_id:
        return redirect(url_for('index'))
    
    # Get emails from MCP server
    try:
        emails_data = await mcp.list_emails(
            account_id=account_id,
            limit=20,
            include_body=False
        )
        
        return render_template('emails.html', 
                             username=session.get('username'),
                             emails=emails_data)
    except Exception as e:
        return f"Error fetching emails: {str(e)}", 500


@app.route('/logout')
async def logout():
    """Logout user"""
    account_id = session.get('account_id')
    
    if account_id:
        # Remove from MCP server cache
        await mcp.logout_account(account_id)
    
    # Clear session
    session.clear()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Flask doesn't natively support async, so we need to use asyncio
    from asgiref.wsgi import WsgiToAsgi
    import uvicorn
    
    # Convert Flask WSGI app to ASGI
    asgi_app = WsgiToAsgi(app)
    
    print("🚀 Starting MCP Web App on http://localhost:5001")
    print("   Make sure MCP server is running on http://localhost:8001")
    
    uvicorn.run(asgi_app, host="0.0.0.0", port=5001)
