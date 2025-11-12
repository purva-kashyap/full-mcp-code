"""
Simplified client for hybrid MCP server - server handles all OAuth complexity
"""
import asyncio
import json
from fastmcp import Client


async def main():
    """Test the hybrid MCP server with simplified flow"""
    
    # Connect to hybrid server (MCP on port 8001)
    async with Client("http://localhost:8001/mcp") as client:
        print("🔗 Connected to hybrid MCP server\n")
        
        # List available tools
        tools_response = await client.list_tools()
        print("📋 Available tools:")
        tools_list = tools_response.tools if hasattr(tools_response, 'tools') else tools_response
        for tool in tools_list:
            tool_name = tool.name if hasattr(tool, 'name') else tool.get('name', 'Unknown')
            tool_desc = tool.description if hasattr(tool, 'description') else tool.get('description', '')
            print(f"   - {tool_name}: {tool_desc}")
        print()
        
        # Just call authenticate_user - server handles everything!
        print("🔐 Authenticating (browser will open automatically)...")
        print("   Please complete authentication in your browser.")
        print("   Waiting for callback...\n")
        
        auth_result = await client.call_tool("authenticate_user", {})
        
        # Parse the result
        auth_content = auth_result.content[0].text
        if isinstance(auth_content, str):
            auth_data = json.loads(auth_content)
        else:
            auth_data = auth_content
        
        if not auth_data.get("success"):
            print(f"❌ Authentication failed: {auth_data.get('error')}")
            print(f"   {auth_data.get('error_description', '')}")
            return
        
        access_token = auth_data["access_token"]
        print("✅ Authentication successful!\n")
        
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
            print("\n✨ Complete! All handled by the hybrid server.")
        else:
            print(f"❌ Failed to get profile: {profile.get('error')}")


if __name__ == "__main__":
    print("🚀 Hybrid MCP Server - Simplified Client Test\n")
    print("Make sure the hybrid server is running:")
    print("   python hybrid_server.py\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
