"""Ultra-simplified client - server handles entire OAuth flow"""
import asyncio
import json
import webbrowser
from fastmcp import Client


async def main():
    print("🚀 Microsoft Email Reader - Ultra-Simplified")
    print("=" * 70)
    
    try:
        async with Client("http://0.0.0.0:8001/mcp/") as client:
            print("\n📡 Connecting to server...")
            
            # Check for existing accounts
            accounts_result = await client.call_tool("list_accounts", {})
            
            # Handle empty response
            accounts = []
            if accounts_result.content and len(accounts_result.content) > 0:
                accounts = json.loads(accounts_result.content[0].text)
            
            account_id = None
            username = None
            
            if accounts and len(accounts) > 0:
                account = accounts[0]
                account_id = account.get('account_id')
                username = account.get('username')
                print(f"✅ Using existing account: {username}")
            
            # Authenticate if needed
            if not account_id:
                print("\n🔐 Starting authentication...")
                
                # Get auth URL from server
                auth_result = await client.call_tool("authenticate_account", {})
                auth_data = json.loads(auth_result.content[0].text)
                
                print(f"\n🌐 Opening browser for authentication...")
                webbrowser.open(auth_data['auth_url'])
                
                print("⏳ Waiting for you to complete authentication in browser...")
                
                # Client tracks state for multi-user support
                wait_result = await client.call_tool("wait_for_callback", {
                    "timeout": 300,
                    "state": auth_data['state']
                })
                callback_data = json.loads(wait_result.content[0].text)
                
                if callback_data.get('status') != 'success':
                    print(f"\n❌ Authentication failed: {callback_data.get('error')}")
                    return
                
                # Complete authentication
                complete_result = await client.call_tool("complete_authentication", {
                    "auth_code": callback_data['auth_code'],
                    "state": callback_data['state']
                })
                result = json.loads(complete_result.content[0].text)
                
                username = result['username']
                account_id = result['account_id']
                print(f"✅ {result.get('message', 'Authenticated')}")
            
            # Read emails - simple!
            print(f"\n📧 Reading emails for {username}...")
            emails_result = await client.call_tool("list_emails", {
                "account_id": account_id,
                "folder": "inbox",
                "limit": 5
            })
            
            emails_data = json.loads(emails_result.content[0].text)
            
            # Handle different response formats
            if isinstance(emails_data, dict):
                emails = emails_data.get('value', [])
            elif isinstance(emails_data, list):
                emails = emails_data
            else:
                emails = []
            
            if not emails:
                print("📭 No emails found")
                return
            
            print(f"\n📬 Latest {len(emails)} emails:\n")
            for i, email in enumerate(emails, 1):
                sender = email.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                print(f"{i}. {email.get('subject', 'No subject')}")
                print(f"   From: {sender}")
                print(f"   Date: {email.get('receivedDateTime', 'Unknown')}\n")
            
            print("✅ Done!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
