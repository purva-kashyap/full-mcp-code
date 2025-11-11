"""
Kubernetes-Ready Flask Web Application for Microsoft 365 Email Reader
Production-ready with proper configuration and session management
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import asyncio
import json
import os
from fastmcp import Client
import redis
from flask_session import Session

app = Flask(__name__)

# Configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-production')
app.config['SESSION_TYPE'] = 'redis'  # Use Redis for session storage across pods
app.config['SESSION_REDIS'] = redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379')
)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Flask-Session
Session(app)

# MCP Server URL - use Kubernetes service name
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://mcp-server-service:8001/mcp/')


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
    
    return render_template('index.html')


@app.route('/api/start-auth', methods=['POST'])
def start_auth():
    """Start OAuth authentication flow"""
    try:
        # Call MCP server to get auth URL
        auth_data = asyncio.run(call_mcp_server('authenticate_account', {}))
        
        # Store state in session for later verification
        session['oauth_state'] = auth_data['state']
        session.modified = True  # Important for Redis session
        
        return jsonify({
            'success': True,
            'auth_url': auth_data['auth_url'],
            'state': auth_data['state']
        })
    except Exception as e:
        app.logger.error(f"Error starting auth: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/check-callback', methods=['POST'])
def check_callback():
    """Poll for OAuth callback completion"""
    try:
        data = request.json
        state = data.get('state')
        
        # Verify state matches
        stored_state = session.get('oauth_state')
        if state != stored_state:
            app.logger.warning(f"State mismatch: {state} != {stored_state}")
            return jsonify({'success': False, 'error': 'Invalid state'}), 400
        
        # Check if callback received (with short timeout for polling)
        callback_data = asyncio.run(call_mcp_server('wait_for_callback', {
            'timeout': 2,  # Short timeout for polling
            'state': state
        }))
        
        if callback_data.get('status') == 'success':
            # Complete authentication
            complete_data = asyncio.run(call_mcp_server('complete_authentication', {
                'auth_code': callback_data['auth_code'],
                'state': callback_data['state']
            }))
            
            if complete_data.get('status') == 'success':
                # Store in session
                session['account_id'] = complete_data['account_id']
                session['username'] = complete_data['username']
                session.modified = True
                
                # Clear oauth state
                session.pop('oauth_state', None)
                
                app.logger.info(f"User authenticated: {complete_data['username']}")
                
                return jsonify({
                    'success': True,
                    'completed': True,
                    'username': complete_data['username']
                })
        
        # Still waiting
        return jsonify({
            'success': True,
            'completed': False,
            'message': 'Waiting for authentication...'
        })
        
    except Exception as e:
        app.logger.error(f"Error checking callback: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get-user-email', methods=['POST'])
def get_user_email():
    """Get user's email address by calling the MCP tool"""
    account_id = session.get('account_id')
    
    if not account_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Call the get_user_profile tool from MCP server
        user_data = asyncio.run(call_mcp_server('get_user_profile', {
            'account_id': account_id
        }))
        
        if user_data:
            # Extract email from profile (could be 'mail' or 'userPrincipalName')
            email = user_data.get('mail') or user_data.get('userPrincipalName')
            
            if email:
                # Store email in session for future use
                session['user_email'] = email
                session.modified = True
                
                app.logger.info(f"Retrieved email for user: {email}")
                print(f"Retrieved email for user: {email}")
                
                return jsonify({
                    'success': True,
                    'email': email
                })
        
        app.logger.error("Could not retrieve user email from profile")
        return jsonify({'success': False, 'error': 'Could not retrieve email'}), 500
        
    except Exception as e:
        app.logger.error(f"Error getting user email: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails', methods=['GET'])
def get_emails():
    """Get user's emails"""
    account_id = session.get('account_id')
    
    if not account_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        folder = request.args.get('folder', 'inbox')
        limit = int(request.args.get('limit', 10))
        
        emails_data = asyncio.run(call_mcp_server('list_emails', {
            'account_id': account_id,
            'folder': folder,
            'limit': limit
        }))
        
        # Handle different response formats
        if isinstance(emails_data, dict):
            emails = emails_data.get('value', [])
        elif isinstance(emails_data, list):
            emails = emails_data
        else:
            emails = []
        
        return jsonify({
            'success': True,
            'emails': emails,
            'count': len(emails)
        })
        
    except Exception as e:
        app.logger.error(f"Error getting emails: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/email/<email_id>')
def get_email(email_id):
    """Get specific email details"""
    account_id = session.get('account_id')
    
    if not account_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        email_data = asyncio.run(call_mcp_server('get_email', {
            'account_id': account_id,
            'email_id': email_id
        }))
        
        return jsonify({
            'success': True,
            'email': email_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting email: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        'status': 'healthy',
        'service': 'webapp',
        'mcp_server': MCP_SERVER_URL
    })


@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username')
    session.clear()
    app.logger.info(f"User logged out: {username}")
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Development mode
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') != 'production')
