# Architecture Comparison: microsoft-mcp vs mcp-server

## Folder Structure Comparison

### microsoft-mcp
```
microsoft-mcp/
├── src/microsoft_mcp/
│   ├── __init__.py
│   ├── mcp_instance.py      # FastMCP("microsoft-365-mcp-server")
│   ├── auth.py              # MSAL + token cache
│   ├── graph.py             # Microsoft Graph API client
│   ├── tools.py             # @mcp.tool definitions
│   └── server.py            # Optional built-in callback (disabled in prod)
├── main.py                  # Entry point
├── requirements.txt
└── .env
```

### mcp-server (NEW - Refactored)
```
mcp-server/
├── src/hybrid_mcp/
│   ├── __init__.py
│   ├── mcp_instance.py      # FastMCP("microsoft-365-hybrid-mcp-server")
│   ├── auth.py              # MSAL + token cache (same pattern)
│   ├── graph.py             # Microsoft Graph API client (same pattern)
│   ├── tools.py             # @mcp.tool definitions (same pattern)
│   └── server.py            # FastAPI for OAuth callbacks
├── main.py                  # Runs both FastAPI + FastMCP
├── client_example.py        # Demo client following list_accounts pattern
├── requirements.txt
└── .env
```

## Key Architectural Similarities

### 1. auth.py Module
Both use identical patterns:

| Feature | microsoft-mcp | mcp-server |
|---------|--------------|------------|
| Token Cache | `~/.microsoft_mcp_token_cache.json` | `~/.hybrid_mcp_token_cache.json` |
| MSAL Client | `ConfidentialClientApplication` | ✅ Same |
| Cache Type | `SerializableTokenCache` | ✅ Same |
| Token Retrieval | `acquire_token_silent(SCOPES, account)` | ✅ Same |
| Auto-refresh | ✅ Built-in via MSAL | ✅ Same |
| Functions | `get_token()`, `list_accounts()`, `authenticate_new_account()`, `complete_authorization_code_flow()` | ✅ Same |

### 2. graph.py Module
Both provide Microsoft Graph API wrapper:

```python
# Both have same structure
async def request(method, endpoint, account_id, ...)
async def get_user_profile(account_id)
async def list_emails(account_id, folder, limit, ...)
async def get_email(email_id, account_id)
async def search_emails(query, account_id, ...)
```

### 3. tools.py Module
Both register MCP tools with @mcp.tool decorator:

**Common Tools:**
- `list_accounts()` - List cached accounts
- `authenticate_account()` - Start OAuth flow
- `complete_authentication()` - Exchange code for token
- `get_user_profile()` - Get user info
- `list_emails()` - List emails from folder
- `get_email()` - Get specific email
- `search_emails()` - Search emails

**Difference:**
- microsoft-mcp: `wait_for_callback()` (blocking wait)
- mcp-server: `check_callback()` (non-blocking poll)

### 4. mcp_instance.py
Both create single FastMCP instance:

```python
from fastmcp import FastMCP
mcp = FastMCP("server-name")
```

## Key Architectural Differences

| Aspect | microsoft-mcp | mcp-server |
|--------|--------------|------------|
| **Callback Handling** | Optional built-in server (disabled in prod) | Dedicated FastAPI server |
| **Architecture** | Single MCP server | Hybrid: FastAPI (8000) + FastMCP (8001) |
| **OAuth Callback** | External callback-server required | Built-in FastAPI server |
| **Deployment** | Needs 2 services (MCP + callback) | 1 service (both in same process) |
| **Ports** | MCP: 8001 | FastAPI: 8000, MCP: 8001 |

## Client Usage Pattern

### Both Follow Same Pattern:

```python
async with Client("http://localhost:8001/mcp") as client:
    # 1. Check for existing accounts
    accounts = await client.call_tool("list_accounts", {})
    
    if accounts:
        # Use existing account - NO RE-AUTH! ✅
        account_id = accounts[0]['account_id']
    else:
        # Authenticate new account
        auth_data = await client.call_tool("authenticate_account", {})
        # ... open browser, wait for callback ...
        complete_data = await client.call_tool("complete_authentication", {...})
        account_id = complete_data['account_id']
    
    # 2. Use account_id for operations
    profile = await client.call_tool("get_user_profile", {"account_id": account_id})
    emails = await client.call_tool("list_emails", {"account_id": account_id, ...})
```

## Token Management - Why No Re-auth?

### MSAL's acquire_token_silent() Magic:

```python
# In auth.py (both projects)
def get_token(account_id):
    app = get_app()  # Loads SerializableTokenCache
    account = app.get_accounts()[0]
    
    # This ONE function does all the magic:
    result = app.acquire_token_silent(SCOPES, account=account)
    #                                  ^^^^^^
    # 1. Checks cache for valid access token
    # 2. If expired, uses refresh token automatically
    # 3. If refresh succeeds, updates cache
    # 4. Returns new access token
    # 5. All transparent to user! ✨
    
    return result["access_token"]
```

### Token Lifecycle:

1. **First Auth**: User authenticates → Gets access token (1h) + refresh token (90 days)
2. **Next 1 hour**: `acquire_token_silent()` returns cached access token
3. **After 1 hour**: `acquire_token_silent()` automatically uses refresh token, gets new access token
4. **Next 90 days**: Keeps auto-refreshing access tokens using refresh token
5. **After 90 days**: Refresh token expires → User needs to re-authenticate

### Cache File Structure:

```json
{
  "AccessToken": {
    "client_id-tenant_id-scope-hash": {
      "secret": "eyJ0eXAi...",
      "expires_on": 1699564800,  // Expires in 1 hour
      ...
    }
  },
  "RefreshToken": {
    "client_id-tenant_id": {
      "secret": "0.AXoA...",
      "expires_on": 1707340800,  // Expires in 90 days
      ...
    }
  },
  "IdToken": {...},
  "Account": {...}
}
```

## Advantages of mcp-server Architecture

✅ **Single Deployment**: Both FastAPI and FastMCP in one process  
✅ **Shared State**: OAuth callbacks and MCP tools share in-memory storage  
✅ **Less Complexity**: No need for separate callback-server service  
✅ **Same Pattern**: Follows microsoft-mcp's auth.py/graph.py/tools.py structure  
✅ **Token Caching**: Identical MSAL-based caching with auto-refresh  

## When to Use Each

### Use microsoft-mcp when:
- Pure MCP server needed
- Callback handled by external service
- Minimal dependencies preferred

### Use mcp-server (hybrid) when:
- Want OAuth callbacks built-in
- Prefer single-service deployment
- Need FastAPI features (REST endpoints, docs, etc.)
- K8s deployment with minimal services

## Migration Path

To migrate from microsoft-mcp to mcp-server:

1. **Copy .env**: Same Azure credentials work
2. **Cache Compatible**: Can share `~/.microsoft_mcp_token_cache.json`
3. **Client Code**: Identical - both use same MCP tools
4. **Callback URL**: Update Azure AD redirect URI to `http://localhost:8000/callback`

## Summary

Both projects use **identical** auth and token management:
- ✅ Same MSAL `ConfidentialClientApplication`
- ✅ Same `SerializableTokenCache`
- ✅ Same `acquire_token_silent()` for auto-refresh
- ✅ Same module structure (auth.py, graph.py, tools.py)
- ✅ Same client usage pattern (list_accounts first)

**Key Difference**: mcp-server adds FastAPI for built-in OAuth callbacks, making it a hybrid single-service deployment.
