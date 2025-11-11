# Authentication Guide

The Microsoft MCP server supports two authentication modes:

## 1. Public Client (PKCE) - Default

**Best for**: Development, desktop applications, scenarios where you cannot securely store a client secret.

**How it works**:
- Uses Authorization Code Flow with PKCE (Proof Key for Code Exchange)
- No client secret required
- More secure for applications that cannot keep secrets confidential

**Setup**:
1. Set only the Client ID:
   ```bash
   export MICROSOFT_MCP_CLIENT_ID="c7379904-73f3-4fe1-b4f5-eeb197ab1ecf"
   ```

2. In Azure AD App Registration:
   - Authentication → Platform: Add "Mobile and desktop applications"
   - Redirect URI: `http://localhost:8000/callback`
   - Allow public client flows: **Yes**

3. Run the server:
   ```bash
   python -m microsoft_mcp.server
   ```

## 2. Confidential Client (Client Secret) - Production

**Best for**: Server-side applications, production environments where you can securely store secrets.

**How it works**:
- Uses standard Authorization Code Flow
- Requires a client secret for token exchange
- More appropriate for server-side applications

**Setup**:
1. Create a client secret in Azure AD:
   - Go to Azure Portal → App Registrations → Your App
   - Certificates & secrets → New client secret
   - Copy the secret value (you can only see it once!)

2. Set both Client ID and Client Secret:
   ```bash
   export MICROSOFT_MCP_CLIENT_ID="your-client-id"
   export MICROSOFT_MCP_CLIENT_SECRET="your-secret-value-here"
   ```

3. In Azure AD App Registration:
   - Authentication → Platform: Add "Web"
   - Redirect URI: `http://localhost:8000/callback`
   - Allow public client flows: **No** (optional)

4. Run the server:
   ```bash
   python -m microsoft_mcp.server
   ```

## Automatic Detection

The server automatically detects which mode to use:

- **If `MICROSOFT_MCP_CLIENT_SECRET` is set**: Uses ConfidentialClientApplication (no PKCE)
- **If `MICROSOFT_MCP_CLIENT_SECRET` is not set**: Uses PublicClientApplication (with PKCE)

No code changes needed - just set or unset the environment variable!

## Security Comparison

| Feature | Public Client (PKCE) | Confidential Client |
|---------|---------------------|-------------------|
| Client Secret Required | ❌ No | ✅ Yes |
| PKCE Required | ✅ Yes | ❌ No |
| Secret Storage | N/A | Must be secure |
| Best For | Development, Desktop | Production, Server-side |
| Azure AD Setup | Simpler | Requires secret management |

## Testing

### Test Public Client (PKCE):
```bash
# Don't set CLIENT_SECRET
unset MICROSOFT_MCP_CLIENT_SECRET
export MICROSOFT_MCP_CLIENT_ID="your-client-id"
python client_authcode.py
```

You should see: `[DEBUG] Using PKCE (public client mode)`

### Test Confidential Client:
```bash
# Set both CLIENT_ID and CLIENT_SECRET
export MICROSOFT_MCP_CLIENT_ID="your-client-id"
export MICROSOFT_MCP_CLIENT_SECRET="your-secret-value"
python client_authcode.py
```

You should see: `[DEBUG] No PKCE (confidential client mode)`

## Troubleshooting

### "client_secret required" error
- Your Azure AD app is configured as confidential (Web platform)
- Either: Set `MICROSOFT_MCP_CLIENT_SECRET` or change Azure AD to Mobile/Desktop platform

### "redirect_uri_mismatch" error
- The redirect URI must exactly match what's registered in Azure AD
- Default: `http://localhost:8000/callback`
- Check both the port (8000) and protocol (http, not https)

### PKCE errors
- Make sure `code_verifier` is being passed for public clients
- Check that Azure AD app allows public client flows

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MICROSOFT_MCP_CLIENT_ID` | ✅ Always | Your Azure AD Application (client) ID |
| `MICROSOFT_MCP_CLIENT_SECRET` | 🔵 Optional | Client secret (triggers confidential client mode) |
| `MICROSOFT_MCP_TENANT_ID` | ❌ No | Defaults to "common" (multi-tenant) |

## Token Cache

Both modes store tokens in the same location:
- Location: `~/.microsoft_mcp_token_cache.json`
- Contains: Access tokens, refresh tokens for all authenticated accounts
- Security: File permissions set to 0600 (user read/write only)
- Persistence: Tokens survive server restarts

To clear authentication:
```bash
rm ~/.microsoft_mcp_token_cache.json
```
