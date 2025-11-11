# Microsoft MCP Server - Setup Guide

A streamable-http MCP server for Microsoft Graph API with OAuth support.

## Features

- ✅ **Email Reading**: List and read emails from your inbox
- ✅ **User Profile**: Get user profile information
- ✅ **OAuth Flow**: Built-in OAuth callback server (no manual URL pasting!)
- ✅ **Streamable HTTP**: Works with any MCP client over HTTP
- ✅ **Multi-Account**: Support for multiple Microsoft accounts

## Quick Start

### 1. Prerequisites

- Python 3.12 or later
- A Microsoft Azure AD application

### 2. Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Microsoft Entra ID → App registrations
2. Click "New registration"
   - Name: `microsoft-mcp-server`
   - Supported account types: Choose based on your needs
     - **Personal Microsoft accounts only**: Select "Personal Microsoft accounts only"
     - **Work/School accounts**: Select appropriate option
3. Click "Register"
4. Note your **Application (client) ID**
5. Go to "Certificates & secrets" → "New client secret"
   - Description: `mcp-server-secret`
   - Expires: Choose duration
   - Click "Add" and **copy the secret value** (you won't see it again!)
6. Go to "Authentication" → "Add a platform" → "Web"
   - Redirect URI: `http://localhost:8000/callback`
   - Click "Configure"
7. Go to "API permissions" → "Add a permission" → "Microsoft Graph" → "Delegated permissions"
   - Add: `User.Read`, `Mail.Read`
   - Click "Add permissions"
   - (Optional) Click "Grant admin consent" if you're an admin

### 3. Installation

```bash
# Clone the repository
git clone https://github.com/purva-kashyap/ms365-mcp-server.git
cd ms365-mcp-server

# Run setup script
./setup.sh
```

This will:
- Create a virtual environment
- Install all required dependencies
- Guide you through configuration

### 4. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Set these values in `.env`:
```bash
MICROSOFT_MCP_CLIENT_ID=your-client-id-here
MICROSOFT_MCP_CLIENT_SECRET=your-client-secret-here
MICROSOFT_MCP_TENANT_ID=consumers  # or your tenant ID for work/school accounts
```

### 5. Running the Server

```bash
# Make sure you're in the project directory
cd ms365-mcp-server

# Option 1: Use the start script (recommended)
./start_server.sh

# Option 2: Manual activation and run
source venv/bin/activate
python3 src/microsoft_mcp/server.py
```

The server will start on:
- **MCP Server**: `http://0.0.0.0:8001/mcp/`
- **OAuth Callback**: `http://localhost:8000/callback`

### 6. Testing the Server

In another terminal:

```bash
# Make sure you're in the project directory
cd ms365-mcp-server

# Use the client script
./run_client.sh

# Or manually
source venv/bin/activate
python3 simple_client.py
```

## Available Tools

The server provides these MCP tools:

1. **`list_accounts`** - List authenticated Microsoft accounts
2. **`authenticate_account`** - Start OAuth authentication flow
3. **`wait_for_callback`** - Wait for OAuth callback (automatic)
4. **`complete_authentication`** - Complete authentication with auth code
5. **`get_user_profile`** - Get user profile information
6. **`list_emails`** - List emails from inbox/folders
7. **`get_email`** - Get specific email details
8. **`search_emails`** - Search for emails

## Usage Example

Once the server is running and you've authenticated:

```python
# The simple_client.py script shows a complete example:
# 1. Connects to the server
# 2. Checks for existing authentication
# 3. If needed, opens browser for OAuth
# 4. Automatically captures callback
# 5. Lists latest emails with details
```

## Architecture

- **Port 8001**: MCP server (FastMCP with streamable-http transport)
- **Port 8000**: OAuth callback server (built-in, automatic)
- **Token Cache**: `~/.microsoft_mcp_token_cache.json`
- **Flow**: Authorization Code Flow with Client Secret (Confidential Client)

## Troubleshooting

### "Port 8000 already in use"
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

### "Port 8001 already in use"
```bash
# Find and kill the process
lsof -ti:8001 | xargs kill -9
```

### "No module named 'fastmcp'"
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Clear authentication cache
```bash
# Remove the token cache to start fresh
rm ~/.microsoft_mcp_token_cache.json
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MICROSOFT_MCP_CLIENT_ID` | Yes | Your Azure AD Application (client) ID |
| `MICROSOFT_MCP_CLIENT_SECRET` | Yes | Your Azure AD Application client secret |
| `MICROSOFT_MCP_TENANT_ID` | No | Tenant ID or "consumers" for personal accounts (default: "consumers") |
| `HOST` | No | Server host (default: "0.0.0.0") |
| `PORT` | No | Server port (default: "8001") |

## Development

### Project Structure
```
microsoft-mcp/
├── src/
│   └── microsoft_mcp/
│       ├── __init__.py
│       ├── server.py         # MCP server with OAuth callback
│       ├── auth.py            # OAuth authentication logic
│       ├── graph.py           # Microsoft Graph API client
│       ├── tools.py           # MCP tool definitions
│       └── mcp_instance.py    # FastMCP instance
├── simple_client.py           # Example client
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment file
├── setup.sh                  # Setup script
├── start_server.sh           # Server start script
└── run_client.sh             # Client start script
```

## License

MIT License - see LICENSE file for details
