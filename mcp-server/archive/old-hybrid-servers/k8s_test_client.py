"""
Client for Kubernetes-compatible hybrid server
Client opens browser (not server), then polls for callback
"""
import asyncio
import json
import webbrowser
from fastmcp import Client


async def main():
    """Test the K8s-compatible hybrid MCP server"""
    
    # Connect to hybrid server (MCP on port 8001)
    async with Client("http://localhost:8001/mcp") as client:
        print("🔗 Connected to hybrid MCP server\n")
        
        # Start authentication - server returns auth URL
        print("🔐 Starting authentication flow...")
        auth_result = await client.call_tool("start_authentication", {
            "callback_base_url": "http://localhost:8000"
        })
        
        auth_content = auth_result.content[0].text
        if isinstance(auth_content, str):
            auth_data = json.loads(auth_content)
        else:
            auth_data = auth_content
        
        auth_url = auth_data["auth_url"]
        state = auth_data["state"]
        
        print(f"📝 State: {state[:20]}...")
        print(f"🌐 Opening browser on CLIENT side (not server)...\n")
        
        # CLIENT opens browser (works in K8s because client has GUI)
        webbrowser.open(auth_url)
        
        print("⏳ Polling for callback (max 120 seconds)...")
        print("   Please complete authentication in your browser.\n")
        
        # Poll for callback
        max_attempts = 60  # 60 attempts * 2 seconds = 120 seconds
        for attempt in range(max_attempts):
            callback_result = await client.call_tool("check_callback", {
                "state": state
            })
            
            callback_content = callback_result.content[0].text
            if isinstance(callback_content, str):
                callback_data = json.loads(callback_content)
            else:
                callback_data = callback_content
            
            if callback_data.get("received"):
                if not callback_data.get("success"):
                    print(f"❌ Authentication failed: {callback_data.get('error')}")
                    return
                
                print("✅ Callback received!\n")
                auth_code = callback_data["auth_code"]
                break
            
            await asyncio.sleep(2)
        else:
            print("❌ Timeout: No callback received")
            return
        
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
            print("\n✨ Complete! Works in Kubernetes too.")
        else:
            print(f"❌ Failed to get profile: {profile.get('error')}")


if __name__ == "__main__":
    print("🚀 Hybrid MCP Server - Kubernetes-Compatible Client\n")
    print("Make sure the hybrid server is running:")
    print("   python hybrid_server_k8s.py\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
