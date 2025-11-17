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
import platform
import subprocess


async def main():
    """Test the hybrid MCP server with microsoft-mcp pattern"""
    
    print("🚀 Hybrid MCP Server - Client (microsoft-mcp pattern)")
    print("="*70)
    
    async with Client("http://localhost:8001/mcp") as client:
        print("\n📡 Connecting to server...")
        print("✅ Connected!\n")

        # List all available tools
        print("🛠️  Available Tools:")
        print("-" * 70)
        tools_result = await client.call_tool("list_tools", {})
        tools_data = json.loads(tools_result.content[0].text)
        
        for idx, tool in enumerate(tools_data, 1):
            print(f"{idx:2}. {tool['name']:30} - {tool['description']}")
        print("-" * 70)
        print()
        
        # Step 1: Check for existing accounts
        print("🔍 Checking for existing authentication...")
        accounts_result = await client.call_tool("list_accounts", {})
        
        accounts = []
        if accounts_result.content and len(accounts_result.content) > 0:
            accounts_data = json.loads(accounts_result.content[0].text)
            if isinstance(accounts_data, list):
                accounts = accounts_data
        
        username = None
        
        # Step 2: Use existing account or authenticate
        if accounts and len(accounts) > 0:
            account = accounts[0]
            username = account.get('username')
            account_id = account.get('account_id')
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
            print(f"🔗 Auth URL: {auth_url}\n")
            print("🌐 Attempting to open browser...")
            
            # Open browser (WSL-compatible method)
            try:   
                system = platform.system()
                
                if system == "Linux":
                    # Check if running in WSL
                    try:
                        with open("/proc/version", "r") as f:
                            if "microsoft" in f.read().lower():
                                # WSL detected - use PowerShell to open in Windows browser
                                subprocess.run([
                                    "powershell.exe", 
                                    "-Command", 
                                    f"Start-Process '{auth_url}'"
                                ], check=True)
                                print("✅ Opened in Windows browser from WSL")
                            else:
                                # Regular Linux - use xdg-open
                                subprocess.run(["xdg-open", auth_url], check=True)
                                print("✅ Opened in Linux browser")
                    except:
                        # Fallback to webbrowser
                        webbrowser.open(auth_url)
                        print("✅ Opened with webbrowser module")
                else:
                    # macOS or Windows
                    webbrowser.open(auth_url)
                    print("✅ Browser should open shortly")
                
                await asyncio.sleep(1)  # Give browser time to open
            except Exception as e:
                print(f"⚠️  Failed to open browser: {e}")
                print("📋 Please COPY the URL above and PASTE it in your browser manually.")
            
            print("\n⏳ Waiting for callback (polling every 2 seconds)...")
            
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
            
            username = complete_data.get('username')
            account_id = complete_data.get('account_id')
            
            print(f"✅ Authenticated as: {username}")
            print(f"   Account ID: {account_id[:20]}...")
            print("   Token cached - next run will use existing account!\n")
        
        # Step 3: Use the username to get profile
        print("👤 Fetching user profile...")
        profile_result = await client.call_tool("get_user_profile", {
            "username": username
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
            "username": username,
            "folder": "inbox",
            "limit": 5,
            "include_body": True
        })
        emails = json.loads(emails_result.content[0].text)

        ##################
        # Handle different response structures
        if isinstance(emails, dict):
            if 'value' in emails:
                emails = emails['value']
            elif '@odata.etag' in emails:
                emails = [emails]
            else:
                emails = [emails]
        elif isinstance(emails, list):
            emails = emails
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


        ###################
        
        print(f"\n📥 Latest {len(emails)} emails from inbox:")
        print("="*80)
        for i, email in enumerate(emails, 1):
            # Extract email details
            sender_info = email.get('from', {}).get('emailAddress', {})
            sender_name = sender_info.get('name', 'Unknown')
            sender_email = sender_info.get('address', 'unknown@email.com')
            
            subject = email.get('subject', 'No subject')
            date = email.get('receivedDateTime', '')
            # Format date nicely
            if date:
                date_formatted = date[:10] + " " + date[11:16]
            else:
                date_formatted = 'Unknown date'
            
            is_read = email.get('isRead', False)
            has_attachments = email.get('hasAttachments', False)
            
            # Get body preview
            body_content = email.get('body', {})
            body_type = body_content.get('contentType', 'text')
            body_text = body_content.get('content', '')
            
            # Truncate body for preview (first 200 chars)
            body_preview = body_text[:200].replace('\n', ' ').replace('\r', ' ').strip()
            if len(body_text) > 200:
                body_preview += "..."
            
            # Get recipients
            to_recipients = email.get('toRecipients', [])
            to_names = [r.get('emailAddress', {}).get('name', 'Unknown') for r in to_recipients[:2]]
            if len(to_recipients) > 2:
                to_names.append(f"+{len(to_recipients) - 2} more")
            
            # Print email details
            read_indicator = "📖" if is_read else "📩"
            attachment_indicator = "📎" if has_attachments else ""
            
            print(f"\n{i}. {read_indicator} {attachment_indicator} [{date_formatted}]")
            print(f"   From: {sender_name} <{sender_email}>")
            if to_names:
                print(f"   To: {', '.join(to_names)}")
            print(f"   Subject: {subject}")
            if body_preview:
                print(f"   Preview: {body_preview}")
            print("-" * 80)
        
        print("="*80)
        print("\n✨ Complete! Pattern summary:")
        print("   1. ✅ Checked list_accounts first")
        if accounts:
            print("   2. ✅ Used existing account (no re-auth needed)")
        else:
            print("   2. ✅ Authenticated new account (cached for next time)")
        print("   3. ✅ Used username for all operations")
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
