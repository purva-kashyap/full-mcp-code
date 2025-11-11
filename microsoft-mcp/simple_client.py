"""Simple client that uses the MCP server's built-in OAuth callback"""
import asyncio
import json
import webbrowser
from fastmcp import Client


async def main():
    print("🚀 Microsoft Email Reader - Simple Client")
    print("=" * 70)
    
    try:
        async with Client("http://0.0.0.0:8001/mcp/") as client:
            print("\n📡 Connecting to server...")
            tools = await client.list_tools()
            tool_count = len(tools) if isinstance(tools, list) else len(tools.tools)
            print(f"✅ Connected! Found {tool_count} tools")
            
            # Check for existing accounts
            print("\n🔍 Checking for existing authentication...")
            accounts_result = await client.call_tool("list_accounts", {})
            
            accounts = []
            if accounts_result.content and len(accounts_result.content) > 0:
                accounts_data = json.loads(accounts_result.content[0].text)
                if isinstance(accounts_data, list):
                    accounts = accounts_data
                elif isinstance(accounts_data, dict):
                    accounts = accounts_data.get('accounts', [accounts_data])
            
            account_id = None
            username = None
            
            if accounts and len(accounts) > 0:
                account = accounts[0]
                if isinstance(account, dict):
                    account_id = account.get('account_id')
                    username = account.get('username')
                    print(f"✅ Using existing account: {username}")
            
            # Authenticate if needed
            if not account_id or not username:
                print("\n❌ No authenticated accounts found")
                print("\n🔐 Starting authentication flow...")
                
                # Get auth URL
                auth_result = await client.call_tool("authenticate_account", {})
                auth_data = json.loads(auth_result.content[0].text)
                
                auth_url = auth_data['auth_url']
                state = auth_data.get('state')  # Get the state for external callback API
                
                print("\n" + "="*70)
                print("📱 MICROSOFT AUTHENTICATION")
                print("="*70)
                print(f"\n🌐 Opening browser for authentication...")
                print(f"   The server will automatically capture the callback!")
                print("="*70)
                
                # Open browser
                webbrowser.open(auth_url)
                
                # Wait for callback using the server's built-in handler
                print("\n⏳ Waiting for authentication callback...")
                
                # Prepare wait_for_callback parameters
                wait_params = {"timeout": 300}
                if state:  # Pass state if using external callback API
                    wait_params["state"] = state
                
                callback_result = await asyncio.wait_for(
                    client.call_tool("wait_for_callback", wait_params),
                    timeout=310.0
                )
                
                callback_data = json.loads(callback_result.content[0].text)
                
                if callback_data.get('status') != 'success':
                    print(f"\n❌ Authentication failed: {callback_data}")
                    return
                
                print("✅ Received callback!")
                
                # Complete authentication
                print("� Completing authentication...")
                complete_result = await asyncio.wait_for(
                    client.call_tool(
                        "complete_authentication",
                        {
                            "auth_code": callback_data['auth_code'],
                            "state": callback_data['state']
                        }
                    ),
                    timeout=30.0
                )
                
                complete_data = json.loads(complete_result.content[0].text)
                
                if complete_data.get('status') != 'success':
                    print(f"\n❌ Authentication failed: {complete_data}")
                    return
                
                username = complete_data['username']
                account_id = complete_data['account_id']
                print(f"✅ Authentication successful!")
                print(f"   Username: {username}")
            
            # Read emails
            print(f"\n📧 Retrieving emails for {username}...")
            
            emails_result = await asyncio.wait_for(
                client.call_tool("list_emails", {
                    "account_id": account_id,
                    "folder": "inbox",
                    "limit": 5,
                    "include_body": True
                }),
                timeout=30.0
            )
            
            emails_data = json.loads(emails_result.content[0].text)
            
            # Handle different response structures
            if isinstance(emails_data, dict):
                if 'value' in emails_data:
                    emails = emails_data['value']
                elif '@odata.etag' in emails_data:
                    emails = [emails_data]
                else:
                    emails = [emails_data]
            elif isinstance(emails_data, list):
                emails = emails_data
            else:
                emails = []
            
            if not emails:
                print("\n📭 No emails found in inbox")
                return
            
            print(f"\n📬 Latest {len(emails)} emails:")
            print("=" * 70)
            
            for i, email in enumerate(emails, 1):
                print(f"\n  {i}. Subject: {email.get('subject', 'No subject')}")
                
                if 'from' in email and 'emailAddress' in email['from']:
                    print(f"     From: {email['from']['emailAddress']['address']}")
                
                print(f"     Date: {email.get('receivedDateTime', 'Unknown')}")
                print(f"     Read: {'Yes' if email.get('isRead', False) else 'No'}")
                
                if email.get('hasAttachments'):
                    print(f"     📎 Has attachments")
                
                # Show email body if available
                if 'body' in email and 'content' in email['body']:
                    body_content = email['body']['content']
                    if len(body_content) > 500:
                        body_content = body_content[:500] + "..."
                    print(f"\n     📄 Body:\n     {body_content}\n")
            
            print("\n✅ Done! Your Microsoft MCP server is working correctly!")
    
    except asyncio.TimeoutError:
        print("\n❌ Request timed out")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
