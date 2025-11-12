# MCP Web App

Simple Flask web application that integrates with the MCP Server to provide Microsoft 365 authentication and email access.

## Features

- ✅ Login with Microsoft account
- ✅ Automatic token caching (no re-authentication for 90 days)
- ✅ List user emails
- ✅ Logout functionality
- ✅ Simple, clean UI

## Prerequisites

1. **MCP Server must be running** on `http://localhost:8001`
   ```bash
   cd ../mcp-server
   python3 main.py
   ```

2. Azure AD app configured (same as MCP server)

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment (`.env` file already created with defaults)

## Running the App

```bash
python3 app.py
```

The app will start on **http://localhost:5000**

## Usage Flow

### First Time User:
1. Open http://localhost:5000
2. Click "Login with Microsoft"
3. Authenticate in browser
4. Redirected back to home page (logged in)
5. Click "List My Emails" to view emails
6. Click "Logout" when done

### Returning User:
1. Open http://localhost:5000
2. **Automatically logged in** (token cached!)
3. Click "List My Emails" directly
4. No re-authentication needed for 90 days!

## How It Works

### Architecture:
```
User Browser → Flask Web App (port 5000) → MCP Server (port 8001) → Microsoft Graph API
```

### MCP Tools Used:
- `list_accounts` - Check if user is already authenticated
- `authenticate_account` - Start OAuth flow
- `check_callback` - Poll for OAuth callback
- `complete_authentication` - Exchange code for token
- `list_emails` - Fetch user emails
- `logout_account` - Clear user token cache

### Routes:
- `/` - Home page (shows login button or user info)
- `/login` - Start OAuth authentication
- `/callback` - Handle OAuth callback (automatic)
- `/emails` - Display user emails
- `/logout` - Logout user

## Configuration

Edit `.env` file:
```env
SECRET_KEY=your-secret-key-here
MCP_SERVER_URL=http://localhost:8001/mcp
CALLBACK_BASE_URL=http://localhost:5000
```

## Project Structure

```
mcp-web-app/
├── app.py              # Main Flask application
├── mcp_client.py       # MCP Server client
├── requirements.txt    # Python dependencies
├── .env               # Configuration
├── .env.example       # Configuration template
├── templates/
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   └── emails.html    # Emails list page
└── README.md          # This file
```

## Notes

- First authentication requires browser interaction
- Subsequent visits use cached tokens (no re-auth!)
- Tokens auto-refresh for 90 days
- Simple session management (server-side)
- Works with multiple users (separate sessions)

## Troubleshooting

**"Connection refused" error:**
- Make sure MCP server is running: `cd ../mcp-server && python3 main.py`

**Authentication fails:**
- Check Azure AD app configuration
- Verify redirect URI includes MCP server callback: `http://localhost:8000/callback`

**Emails not loading:**
- Ensure user has Mail.Read permission granted
- Check MCP server logs for errors
