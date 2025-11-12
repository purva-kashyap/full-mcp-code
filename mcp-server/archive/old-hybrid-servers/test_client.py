"""
Simple client example for hybrid MCP server
"""
import asyncio
import json
import webbrowser
from fastmcp import Client


async def main():
    """Test the hybrid MCP server"""
    
    # Connect to hybrid server (MCP on port 8001)
    async with Client("http://localhost:8001/mcp") as client:
        print("🔗 Connected to hybrid MCP server\n")
        
        # List available tools
        tools_response = await client.list_tools()
        print("📋 Available tools:")
        # Handle different response formats
        tools_list = tools_response.tools if hasattr(tools_response, 'tools') else tools_response
        for tool in tools_list:
            tool_name = tool.name if hasattr(tool, 'name') else tool.get('name', 'Unknown')
            tool_desc = tool.description if hasattr(tool, 'description') else tool.get('description', '')
            print(f"   - {tool_name}: {tool_desc}")
        print()
        
        # Start authentication
        print("🔐 Starting authentication flow...")
        auth_result = await client.call_tool("authenticate_account", {
            "callback_base_url": "http://localhost:8000"
        })
        
        # Parse the result - it might be text or dict
        result_content = auth_result.content[0].text
        if isinstance(result_content, str):
            import json
            result_data = json.loads(result_content)
        else:
            result_data = result_content
            
        auth_url = result_data["auth_url"]
        state = result_data["state"]
        
        print(f"📝 State: {state[:20]}...")
        print(f"🌐 Opening browser for authentication...\n")
        
        # Open browser for user to authenticate
        webbrowser.open(auth_url)
        
        print("⏳ Waiting for callback (max 120 seconds)...")
        print("   Please complete authentication in your browser.\n")
        
        # Wait for callback
        callback_result = await client.call_tool("wait_for_callback", {
            "state": state,
            "timeout": 120
        })
        
        callback_content = callback_result.content[0].text
        if isinstance(callback_content, str):
            callback_data = json.loads(callback_content)
        else:
            callback_data = callback_content
        
        if not callback_data.get("success"):
            print(f"❌ Authentication failed: {callback_data.get('error')}")
            return
        
        print("✅ Callback received!\n")
        
        auth_code = callback_data["auth_code"]
        
        # Complete authentication
        print("🔑 Exchanging code for access token...")
        token_result = await client.call_tool("complete_authentication", {
            "auth_code": auth_code,
            "callback_base_url": "http://localhost:8000"
        })
        
        token_content = token_result.content[0].text
        if isinstance(token_content, str):
            token_data = json.loads(token_content)
        else:
            token_data = token_content
        
        if not token_data.get("success"):
            print(f"❌ Token exchange failed: {token_data.get('error')}")
            return
        
        access_token = token_data["access_token"]
        print("✅ Access token obtained!\n")
        
        # Get user profile
        print("👤 Fetching user profile...")
        profile_result = await client.call_tool("get_user_profile", {
            "access_token": access_token
        })
        
        profile_content = profile_result.content[0].text
        if isinstance(profile_content, str):
            profile = json.loads(profile_content)
        else:
            profile = profile_content
        
        if "error" not in profile:
            print("\n" + "="*50)
            print("📧 User Profile:")
            print("="*50)
            print(f"Name: {profile.get('displayName', 'N/A')}")
            print(f"Email: {profile.get('mail') or profile.get('userPrincipalName', 'N/A')}")
            print(f"Job Title: {profile.get('jobTitle', 'N/A')}")
            print(f"Office: {profile.get('officeLocation', 'N/A')}")
            print("="*50)
        else:
            print(f"❌ Failed to get profile: {profile.get('error')}")


if __name__ == "__main__":
    print("🚀 Hybrid MCP Server - Client Test\n")
    print("Make sure the hybrid server is running:")
    print("   python hybrid_server.py\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
