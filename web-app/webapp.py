"""
Flask Web Application for Microsoft 365 Email Reader
Uses the MCP server as backend to authenticate and read emails
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import asyncio
import json
from fastmcp import Client
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # For session management

# MCP Server URL
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
    
    return render_template('index.html')


@app.route('/api/start-auth', methods=['POST'])
def start_auth():
    """Start OAuth authentication flow"""
    try:
        # Call MCP server to get auth URL
        auth_data = asyncio.run(call_mcp_server('authenticate_account', {}))
        
        # Store state in session for later verification
        session['oauth_state'] = auth_data['state']
        
        return jsonify({
            'success': True,
            'auth_url': auth_data['auth_url'],
            'state': auth_data['state']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/check-callback', methods=['POST'])
def check_callback():
    """Poll for OAuth callback completion"""
    try:
        data = request.json
        state = data.get('state')
        
        # Verify state matches
        if state != session.get('oauth_state'):
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
                
                return jsonify({
                    'success': True,
                    'email': email
                })
        
        return jsonify({'success': False, 'error': 'Could not retrieve email'}), 500
        
    except Exception as e:
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
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
