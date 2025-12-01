# Application MCP Server

MCP server that uses **Application Permissions** with **Client Credentials Flow** to access Microsoft Graph API. This allows the application to act on its own behalf (not on behalf of a user) to access any user's mailbox in the organization.

## Key Differences from Delegated Permissions

| Feature | Delegated Permissions (mcp-server) | Application Permissions (this project) |
|---------|-----------------------------------|----------------------------------------|
| **Authentication Flow** | Authorization Code Flow | Client Credentials Flow |
| **User Interaction** | Required (user must sign in) | Not required |
| **Access Scope** | Only signed-in user's data | Any user's data in the organization |
| **Permission Type** | Delegated (e.g., `Mail.Read`) | Application (e.g., `Mail.Read`) |
| **Admin Consent** | Optional (user can consent) | **Required** |
| **Token Context** | On behalf of a user | On behalf of the application |
| **Tenant ID** | Can use "common" or "consumers" | Must use specific tenant ID |

## Azure Portal Setup

### 1. Create App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Enter a name (e.g., "Application MCP Server")
5. Select **Accounts in this organizational directory only**
6. Click **Register**

### 2. Configure Application Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** > **Microsoft Graph** > **Application permissions**
3. Add the following permissions:
   - `Mail.Read` - Read mail in all mailboxes
   - `User.Read.All` - Read all users' full profiles
4. Click **Grant admin consent for [Your Organization]** ✅ (Admin must approve)

**Important**: Application permissions require admin consent. Without it, the app cannot access any data.

### 3. Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and set expiration
4. Copy the **Value** (you won't see it again!)

### 4. Get Tenant ID

1. Go to **Azure Active Directory** > **Overview**
2. Copy the **Tenant ID**

## Installation

```bash
cd application-mcp-server
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your Azure app details:
```env
AZURE_CLIENT_ID=your-application-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id  # MUST be specific tenant, not "common"
```

## Running the Server

```bash
python main.py
```

The server will start:
- FastAPI: http://localhost:8000
- MCP endpoint: http://localhost:8001/mcp
- Health check: http://localhost:8000/health

## Usage

### Client Example

```python
import asyncio
import json
from fastmcp import Client


async def main():
    async with Client("http://localhost:8001/mcp") as client:
        # No authentication needed - app uses its own credentials
        
        # List users in the organization
        result = await client.call_tool("list_users", {"limit": 5})
        users = json.loads(result.content[0].text)
        print("Users:", users)
        
        # Get a specific user's emails
        user_email = "user@contoso.com"
        result = await client.call_tool("list_emails", {
            "user_email": user_email,
            "folder": "inbox",
            "limit": 5
        })
        emails = json.loads(result.content[0].text)
        print(f"Emails for {user_email}:", emails)


asyncio.run(main())
```

## Available MCP Tools

### `list_users`
List users in the organization (useful for discovering available mailboxes).

**Parameters:**
- `limit` (int, optional): Maximum users to return (default: 10)

### `get_user_profile`
Get user profile information for any user in the organization.

**Parameters:**
- `user_email` (str, required): User's email or userPrincipalName

### `list_emails`
List emails from any user's mailbox.

**Parameters:**
- `user_email` (str, required): User's email or userPrincipalName
- `folder` (str, optional): Folder name - inbox, sent, drafts, deleted, junk (default: inbox)
- `limit` (int, optional): Max emails to return (default: 10)
- `include_body` (bool, optional): Include email body (default: true)

### `get_email`
Get full details of a specific email.

**Parameters:**
- `user_email` (str, required): User's email or userPrincipalName
- `email_id` (str, required): Email message ID

### `search_emails`
Search emails in any user's mailbox.

**Parameters:**
- `user_email` (str, required): User's email or userPrincipalName
- `query` (str, required): Search query
- `limit` (int, optional): Max results (default: 10)

## Architecture

```
application-mcp-server/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── .env.example                     # Environment template
└── src/
    └── application_mcp/
        ├── __init__.py
        ├── auth.py                  # Client Credentials flow
        ├── graph.py                 # Graph API client (uses /users/{email})
        ├── server.py                # FastAPI server (health checks only)
        ├── mcp_instance.py          # FastMCP instance
        └── tools.py                 # MCP tools
```

## Security Considerations

⚠️ **Important**: This approach grants the application access to **all mailboxes** in the organization.

- Only use in trusted environments
- Apply principle of least privilege
- Consider implementing additional access controls
- Audit access regularly
- Rotate client secrets periodically
- Monitor for unusual access patterns

## Troubleshooting

### "AADSTS70011: The provided value for the input parameter 'scope' is not valid"

- Make sure you're using **application permissions**, not delegated permissions
- Use `.default` scope: `https://graph.microsoft.com/.default`

### "Insufficient privileges to complete the operation"

- Ensure **admin consent** has been granted for the application permissions
- Check that Mail.Read application permission (not delegated) is configured

### "AADSTS90002: Tenant not found"

- Make sure `AZURE_TENANT_ID` is your organization's specific tenant ID
- Cannot use "common" or "consumers" with application permissions

### "invalid_client: The client secret has expired"

- Client secret has expired - create a new one in Azure Portal
- Update `.env` with the new secret

## Comparison with mcp-server

**Use mcp-server (Delegated Permissions) when:**
- Users should only access their own data
- User consent is sufficient
- You want audit trail of which user performed actions
- Multi-tenant scenarios

**Use application-mcp-server (Application Permissions) when:**
- Server-to-server scenarios
- Background services/daemons
- Admin/monitoring tools
- Need to access multiple users' data without user interaction
- Single-tenant organization

## License

MIT
