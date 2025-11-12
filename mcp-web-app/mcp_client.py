"""MCP Client for interacting with MCP Server tools"""
from fastmcp.client import Client as FastMCPClient
import json


class MCPClient:
    """Simple client to interact with MCP Server"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = None
    
    async def _ensure_client(self):
        """Ensure FastMCP client is created and connected"""
        if self.client is None:
            self.client = FastMCPClient(self.server_url)
            await self.client.__aenter__()
    
    async def _call_tool(self, tool_name: str, arguments: dict = None):
        """Call an MCP tool"""
        await self._ensure_client()
        result = await self.client.call_tool(tool_name, arguments or {})
        
        # FastMCP client returns a CallToolResult object with a 'content' attribute
        # The content is a list of TextContent objects
        if result and hasattr(result, 'content') and result.content:
            text_content = result.content[0].text
            # Parse JSON if it's a string
            if isinstance(text_content, str):
                import json
                return json.loads(text_content)
            return text_content
        
        return None
    
    async def list_accounts(self):
        """List all authenticated accounts"""
        result = await self._call_tool("list_accounts")
        # Result is already parsed by FastMCP client
        return result if isinstance(result, list) else []
    
    async def authenticate_account(self):
        """Start authentication flow"""
        result = await self._call_tool("authenticate_account")
        return result if isinstance(result, dict) else {}
    
    async def check_callback(self, state: str):
        """Check if OAuth callback has been received"""
        result = await self._call_tool("check_callback", {"state": state})
        return result if isinstance(result, dict) else {}
    
    async def complete_authentication(self, auth_code: str):
        """Complete authentication with authorization code"""
        result = await self._call_tool("complete_authentication", {"auth_code": auth_code})
        return result if isinstance(result, dict) else {}
    
    async def logout_account(self, account_id: str):
        """Logout an account"""
        result = await self._call_tool("logout_account", {"account_id": account_id})
        return result if isinstance(result, dict) else {}
    
    async def get_user_profile(self, account_id: str):
        """Get user profile"""
        result = await self._call_tool("get_user_profile", {"account_id": account_id})
        return result if isinstance(result, dict) else {}
    
    async def list_emails(self, account_id: str, limit: int = 20, include_body: bool = False):
        """List user emails"""
        result = await self._call_tool("list_emails", {
            "account_id": account_id,
            "limit": limit,
            "include_body": include_body
        })
        return result if isinstance(result, list) else []
    
    async def close(self):
        """Close the client"""
        if self.client:
            await self.client.__aexit__(None, None, None)
