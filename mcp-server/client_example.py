"""
Client following microsoft-mcp pattern:
1. Check list_accounts first
2. Only authenticate if no accounts exist
3. Use account_id for all operations
"""
import asyncio
import json
import webbrowser
from fastmcp import Client


async def main():
    """Test the hybrid MCP server with microsoft-mcp pattern"""
    
    print("🚀 Hybrid MCP Server - Client (microsoft-mcp pattern)")
    print("="*70)
    
    async with Client("http://localhost:8001/mcp") as client:
        print("\n📡 Connecting to server...")
        print("✅ Connected!\n")
        
        # Step 1: Check for existing accounts
        print("🔍 Checking for existing authentication...")
        accounts_result = await client.call_tool("list_accounts", {})
        
        accounts = []
        if accounts_result.content and len(accounts_result.content) > 0:
            accounts_data = json.loads(accounts_result.content[0].text)
            if isinstance(accounts_data, list):
                accounts = accounts_data
        
        account_id = None
        username = None
        
        # Step 2: Use existing account or authenticate
        if accounts and len(accounts) > 0:
            account = accounts[0]
            account_id = account.get('account_id')
            username = account.get('username')
            print(f"✅ Using existing account: {username}")
            print(f"   Account ID: {account_id[:20]}...")
            print("   (Token will be auto-refreshed if needed)\n")
        else:
            # No accounts found - need to authenticate
            print("❌ No authenticated accounts found\n")
            print("🔐 Starting authentication flow...")
            
            # Get auth URL
            auth_result = await client.call_tool("authenticate_account", {})
            auth_data = json.loads(auth_result.content[0].text)
            
            auth_url = auth_data['auth_url']
            state = auth_data['state']
            
            print(f"📝 State: {state[:20]}...")
            print("🌐 Opening browser for authentication...\n")
            
            # Open browser
            webbrowser.open(auth_url)
            
            print("⏳ Waiting for callback (polling every 2 seconds)...")
            
            # Poll for callback
            max_attempts = 60  # 120 seconds total
            auth_code = None
            for attempt in range(max_attempts):
                check_result = await client.call_tool("check_callback", {"state": state})
                check_data = json.loads(check_result.content[0].text)
                
                if check_data.get("received"):
                    if not check_data.get("success"):
                        print(f"\n❌ Authentication failed: {check_data.get('error')}")
                        return
                    
                    print("✅ Callback received!\n")
                    auth_code = check_data["auth_code"]
                    break
                
                await asyncio.sleep(2)
            
            if not auth_code:
                print("❌ Timeout: No callback received")
                return
            
            # Complete authentication
            print("🔑 Completing authentication...")
            complete_result = await client.call_tool("complete_authentication", {
                "auth_code": auth_code
            })
            complete_data = json.loads(complete_result.content[0].text)
            
            account_id = complete_data.get('account_id')
            username = complete_data.get('username')
            
            print(f"✅ Authenticated as: {username}")
            print(f"   Account ID: {account_id[:20]}...")
            print("   Token cached - next run will use existing account!\n")
        
        # Step 3: Use the account to get profile
        print("👤 Fetching user profile...")
        profile_result = await client.call_tool("get_user_profile", {
            "account_id": account_id
        })
        profile = json.loads(profile_result.content[0].text)
        
        print("\n" + "="*50)
        print("📧 User Profile:")
        print("="*50)
        print(f"Name: {profile.get('displayName', 'N/A')}")
        print(f"Email: {profile.get('mail') or profile.get('userPrincipalName', 'N/A')}")
        print(f"Job Title: {profile.get('jobTitle', 'N/A')}")
        print(f"Office: {profile.get('officeLocation', 'N/A')}")
        print("="*50)
        
        # Step 4: List some emails
        print("\n📬 Fetching latest emails...")
        emails_result = await client.call_tool("list_emails", {
            "account_id": account_id,
            "folder": "inbox",
            "limit": 5,
            "include_body": False
        })
        emails = json.loads(emails_result.content[0].text)
        
        print(f"\n📥 Latest {len(emails)} emails from inbox:")
        print("="*70)
        for i, email in enumerate(emails, 1):
            sender = email.get('from', {}).get('emailAddress', {}).get('name', 'Unknown')
            subject = email.get('subject', 'No subject')
            date = email.get('receivedDateTime', '')[:10]
            print(f"{i}. [{date}] {sender}")
            print(f"   {subject}")
            print()
        
        print("="*70)
        print("\n✨ Complete! Pattern summary:")
        print("   1. ✅ Checked list_accounts first")
        if accounts:
            print("   2. ✅ Used existing account (no re-auth needed)")
        else:
            print("   2. ✅ Authenticated new account (cached for next time)")
        print("   3. ✅ Used account_id for all operations")
        print("   4. ✅ Token auto-refreshed via acquire_token_silent")


if __name__ == "__main__":
    print("Make sure the hybrid server is running:")
    print("   python main.py\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
