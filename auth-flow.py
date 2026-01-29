from flask import Flask, redirect, request, session, jsonify, render_template_string
from msal import ConfidentialClientApplication
import os
import secrets
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ============================================
# CONFIGURATION - Replace with your values
# ============================================
CLIENT_ID = "your-client-id-here"
CLIENT_SECRET = "your-client-secret-here"
TENANT_ID = "your-tenant-id-here"  # or "common" for multi-tenant
REDIRECT_URI = "http://localhost:5000/auth/callback"  # Update for production

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Scopes - offline_access is required for refresh_token
SCOPES = [
    "User.Read",
    "offline_access"  # Required to get refresh_token
]

# Initialize MSAL Confidential Client
msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

# ============================================
# IN-MEMORY STORAGE (Replace with database in production)
# ============================================
user_tokens = {}  # Format: {user_id: {access_token, refresh_token, expires_at}}


# ============================================
# ROUTES
# ============================================

@app.route("/")
def home():
    """Home page with onboarding link"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Microsoft Entra Onboarding</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #0078d4;
            }
            .btn {
                display: inline-block;
                padding: 12px 24px;
                background-color: #0078d4;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
            }
            .btn:hover {
                background-color: #005a9e;
            }
            .info {
                background-color: #e7f3ff;
                padding: 15px;
                border-left: 4px solid #0078d4;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Our Application</h1>
            <div class="info">
                <p><strong>What happens when you click the button below:</strong></p>
                <ul>
                    <li>You'll be redirected to Microsoft login</li>
                    <li>Sign in with your organizational account (SSO supported)</li>
                    <li>Grant consent to the requested permissions</li>
                    <li>We'll securely capture and store your tokens</li>
                </ul>
            </div>
            <a href="/onboard" class="btn">Start Onboarding</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/onboard")
def onboard():
    """Initiate the authorization code flow"""
    try:
        # Use initiate_auth_code_flow (recommended - handles PKCE & state)
        flow = msal_app.initiate_auth_code_flow(
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        if "error" in flow:
            return jsonify({
                "error": "Failed to initiate auth flow",
                "details": flow.get("error_description")
            }), 500
        
        # Store the flow in session for validation in callback
        session["auth_flow"] = flow
        
        # Redirect user to Microsoft login page
        return redirect(flow["auth_uri"])
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/auth/callback")
def callback():
    """Handle the callback from Microsoft and exchange code for tokens"""
    try:
        # Retrieve the flow from session
        flow = session.get("auth_flow", {})
        
        if not flow:
            return jsonify({"error": "No auth flow found in session"}), 400
        
        # Exchange the authorization code for tokens
        result = msal_app.acquire_token_by_auth_code_flow(
            flow,
            request.args  # Contains auth code and state
        )
        
        # Check for errors
        if "error" in result:
            return jsonify({
                "error": result.get("error"),
                "description": result.get("error_description")
            }), 400
        
        # Extract tokens
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        id_token_claims = result.get("id_token_claims", {})
        expires_in = result.get("expires_in", 3600)
        
        # Get user information
        user_id = id_token_claims.get("oid")  # Object ID (unique user identifier)
        user_email = id_token_claims.get("preferred_username") or id_token_claims.get("email")
        user_name = id_token_claims.get("name")
        
        # Calculate token expiration
        expires_at = datetime.now().timestamp() + expires_in
        
        # Store tokens (In production, encrypt and store in database)
        user_tokens[user_id] = {
            "user_id": user_id,
            "email": user_email,
            "name": user_name,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat()
        }
        
        # Clear the session
        session.pop("auth_flow", None)
        
        # Store user_id in session for subsequent requests
        session["user_id"] = user_id
        
        # Success page
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Onboarding Success</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .success {{
                    color: #107c10;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                .user-info {{
                    background-color: #f0f0f0;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #0078d4;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✓ Onboarding Successful!</div>
                <p>Your tokens have been securely captured and stored.</p>
                <div class="user-info">
                    <strong>User Information:</strong><br>
                    Name: {user_name}<br>
                    Email: {user_email}<br>
                    User ID: {user_id}
                </div>
                <a href="/profile" class="btn">View Profile</a>
                <a href="/tokens" class="btn">View Tokens (Debug)</a>
            </div>
        </body>
        </html>
        """
        return render_template_string(html)
        
    except Exception as e:
        return jsonify({
            "error": "Authentication failed",
            "details": str(e)
        }), 500


@app.route("/profile")
def profile():
    """Fetch user profile using the stored access token"""
    try:
        user_id = session.get("user_id")
        
        if not user_id or user_id not in user_tokens:
            return redirect("/")
        
        user_data = user_tokens[user_id]
        access_token = user_data["access_token"]
        
        # Call Microsoft Graph API to get user profile
        import requests
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
        
        if response.status_code == 200:
            profile_data = response.json()
            return jsonify({
                "message": "Profile fetched successfully",
                "profile": profile_data
            })
        else:
            return jsonify({
                "error": "Failed to fetch profile",
                "status_code": response.status_code,
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tokens")
def view_tokens():
    """Debug endpoint to view stored tokens (Remove in production!)"""
    user_id = session.get("user_id")
    
    if not user_id or user_id not in user_tokens:
        return jsonify({"error": "No tokens found"}), 404
    
    token_data = user_tokens[user_id].copy()
    
    # Mask tokens for security (show only first/last few characters)
    if token_data.get("access_token"):
        token_data["access_token"] = f"{token_data['access_token'][:20]}...{token_data['access_token'][-20:]}"
    if token_data.get("refresh_token"):
        token_data["refresh_token"] = f"{token_data['refresh_token'][:20]}...{token_data['refresh_token'][-20:]}"
    
    return jsonify(token_data)


@app.route("/refresh")
def refresh_token():
    """Refresh the access token using the refresh token"""
    try:
        user_id = session.get("user_id")
        
        if not user_id or user_id not in user_tokens:
            return jsonify({"error": "No user session found"}), 404
        
        user_data = user_tokens[user_id]
        refresh_token = user_data.get("refresh_token")
        
        if not refresh_token:
            return jsonify({"error": "No refresh token available"}), 400
        
        # Use refresh token to get new access token
        result = msal_app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=SCOPES
        )
        
        if "error" in result:
            return jsonify({
                "error": result.get("error"),
                "description": result.get("error_description")
            }), 400
        
        # Update stored tokens
        user_tokens[user_id]["access_token"] = result.get("access_token")
        user_tokens[user_id]["expires_at"] = datetime.now().timestamp() + result.get("expires_in", 3600)
        
        # Update refresh token if a new one is provided
        if result.get("refresh_token"):
            user_tokens[user_id]["refresh_token"] = result.get("refresh_token")
        
        return jsonify({
            "message": "Token refreshed successfully",
            "expires_in": result.get("expires_in")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logout")
def logout():
    """Clear session and tokens"""
    user_id = session.get("user_id")
    
    if user_id and user_id in user_tokens:
        del user_tokens[user_id]
    
    session.clear()
    
    return jsonify({"message": "Logged out successfully"})


# ============================================
# RUN APPLICATION
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("Microsoft Entra ID Onboarding Server")
    print("=" * 60)
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Make sure this is registered in your Entra app!")
    print("=" * 60)
    print("\nStarting server on http://localhost:5000")
    print("Open your browser and go to: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000)