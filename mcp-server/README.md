# Hybrid FastMCP + FastAPI Server

A unified MCP server that combines FastMCP tools with FastAPI OAuth callback handling in a single application.

## Features

- ✅ **FastMCP Tools**: Authenticate, get user profile, access Microsoft Graph
- ✅ **Built-in OAuth Callback**: No separate callback server needed
- ✅ **Single Port**: Both MCP and OAuth on one endpoint
- ✅ **In-Memory Storage**: OAuth state management with automatic expiry
- ✅ **Health Checks**: Built-in health endpoint for monitoring
- ✅ **Easy Integration**: Works with existing web apps and clients

## Architecture

```
┌─────────────────────────────────────────┐
│     Hybrid Server (Port 8000)           │
│  ┌─────────────┬──────────────────┐     │
│  │  FastAPI    │    FastMCP       │     │
│  │  - /oauth   │    - /mcp        │     │
│  │  - /health  │    - tools       │     │
│  └─────────────┴──────────────────┘     │
│          Shared In-Memory Store         │
└─────────────────────────────────────────┘
```

## Setup

1. **Copy environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   python hybrid_server.py
   ```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info |
| `/health` | GET | Health check |
| `/oauth/callback` | GET | OAuth redirect URI |
| `/api/callback/{state}` | GET | Poll for callback status |
| `/mcp` | POST | MCP protocol endpoint |

## MCP Tools

### 1. `authenticate_account`
Start OAuth flow and get authorization URL.

**Parameters**:
- `callback_base_url` (string): Base URL for callbacks (e.g., `http://localhost:8000`)

**Returns**:
```json
{
  "auth_url": "https://login.microsoftonline.com/...",
  "state": "random-state-token",
  "message": "Open the auth_url in a browser"
}
```

### 2. `wait_for_callback`
Wait for OAuth callback to complete.

**Parameters**:
- `state` (string): State from `authenticate_account`
- `timeout` (int): Max seconds to wait (default: 60)

**Returns**:
```json
{
  "success": true,
  "auth_code": "authorization-code",
  "state": "state-token"
}
```

### 3. `complete_authentication`
Exchange authorization code for access token.

**Parameters**:
- `auth_code` (string): Authorization code from callback
- `callback_base_url` (string): Same base URL used in authenticate

**Returns**:
```json
{
  "success": true,
  "access_token": "eyJ0eXAi...",
  "expires_in": 3600
}
```

### 4. `get_user_profile`
Get user information from Microsoft Graph.

**Parameters**:
- `access_token` (string): OAuth access token

**Returns**:
```json
{
  "displayName": "John Doe",
  "mail": "john@example.com",
  "userPrincipalName": "john@example.com"
}
```

## Usage Example

### Python Client

```python
from fastmcp import Client
import webbrowser

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        # 1. Start authentication
        auth_result = await client.call_tool("authenticate_account", {
            "callback_base_url": "http://localhost:8000"
        })
        
        auth_url = auth_result.content[0].text["auth_url"]
        state = auth_result.content[0].text["state"]
        
        # 2. Open browser for user to authenticate
        webbrowser.open(auth_url)
        
        # 3. Wait for callback
        callback_result = await client.call_tool("wait_for_callback", {
            "state": state,
            "timeout": 120
        })
        
        auth_code = callback_result.content[0].text["auth_code"]
        
        # 4. Complete authentication
        token_result = await client.call_tool("complete_authentication", {
            "auth_code": auth_code,
            "callback_base_url": "http://localhost:8000"
        })
        
        access_token = token_result.content[0].text["access_token"]
        
        # 5. Get user profile
        profile = await client.call_tool("get_user_profile", {
            "access_token": access_token
        })
        
        print(f"Logged in as: {profile.content[0].text['displayName']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Web Application Integration

Your web app can use this hybrid server instead of separate callback and MCP servers:

```python
# webapp.py - Update MCP server URL
MCP_SERVER_URL = "http://localhost:8000/mcp"  # Single endpoint!

# The OAuth callback is now handled by the same server
# No need for separate callback-server anymore
```

## Advantages Over Separate Servers

| Feature | Separate Servers | Hybrid Server |
|---------|-----------------|---------------|
| **Deployment** | 2+ processes | 1 process |
| **Ports** | 2+ ports | 1 port |
| **Configuration** | Multiple configs | Single config |
| **Development** | Start multiple servers | `python hybrid_server.py` |
| **Kubernetes** | 2+ deployments | 1 deployment |
| **State Sharing** | Network calls | In-memory |

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hybrid-mcp-server
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: hybrid-server
        image: your-registry/hybrid-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: client-id
        - name: AZURE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: client-secret
```

⚠️ **Note for K8s**: For production with multiple replicas, replace in-memory storage with Redis (similar to webapp_k8s.py pattern).

## Comparison with Original Architecture

### Original (3 Servers)
```
microsoft-mcp (port 8001) ─┐
callback-server (port 3000) ├─> web-app (port 5000)
                            │
```

### Hybrid (2 Servers)
```
hybrid-server (port 8000) ──> web-app (port 5000)
```

### Fully Integrated (1 Server)
You could even merge the web-app into this hybrid server by adding Flask routes to the FastAPI app!

## Development vs Production

- **Development**: Run locally with `python hybrid_server.py`
- **Production**: 
  - Use Redis for callback storage (if multiple replicas)
  - Add proper logging and monitoring
  - Use environment-based configuration
  - Deploy behind HTTPS with proper domain

## Troubleshooting

**Q: MCP endpoint not responding?**
- Check if it's mounted at `/mcp` or running on separate port `:8001`
- Look for console messages during startup

**Q: OAuth callback not being received?**
- Ensure redirect URI in Azure AD matches `http://localhost:8000/oauth/callback`
- Check browser network tab for redirect issues

**Q: Timeout waiting for callback?**
- Increase timeout parameter in `wait_for_callback`
- Check if user actually completed authentication in browser

## Next Steps

1. Add more Microsoft Graph tools (emails, calendar, etc.)
2. Implement token caching and refresh
3. Add Redis support for multi-replica deployments
4. Create Dockerfile for containerization
5. Add comprehensive error handling and logging
