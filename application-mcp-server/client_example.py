"""
Example client for Application MCP Server

This demonstrates how to use the MCP server with application permissions.
No user authentication is required - the app uses its own credentials.
"""
import asyncio
import json
from fastmcp import Client


async def main():
    """Test the Application MCP Server"""
    
    print("🚀 Application MCP Server - Client Example")
    print("="*70)
    print("Note: This uses application permissions - no user login required!")
    print()
    
    async with Client("http://localhost:8001/mcp") as client:
        print("📡 Connecting to server...")
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
        
        # Step 1: List users in the organization
        print("👥 Listing users in the organization...")
        users_result = await client.call_tool("list_users", {"limit": 5})
        users = json.loads(users_result.content[0].text)
        
        print(f"\nFound {len(users)} users:")
        for user in users:
            display_name = user.get('displayName', 'N/A')
            email = user.get('email', 'N/A')
            upn = user.get('userPrincipalName', 'N/A')
            is_external = '#EXT#' in upn
            user_type = '(External Guest)' if is_external else '(Organization User)'
            print(f"  - {display_name} {user_type}")
            print(f"    Email: {email}")
            print(f"    UPN: {upn}")
        print()
        
        # Step 2: Pick a user (or ask for input)
        if not users:
            print("❌ No users found in organization")
            return
        
        # Filter out external users and find an organization user with a mailbox
        org_users = [u for u in users if '#EXT#' not in u.get('userPrincipalName', '')]
        
        if not org_users:
            print("⚠️  Only external guest users found. They may not have mailboxes.")
            print("   Using first user anyway, but this might fail...")
            selected_user = users[0]
        else:
            print(f"✅ Found {len(org_users)} organization user(s) with potential mailboxes")
            selected_user = org_users[0]
        
        # Use userPrincipalName for API calls (more reliable than email)
        user_email = selected_user.get('userPrincipalName') or selected_user.get('email')
        
        # Uncomment to manually specify:
        # user_email = input("Enter user email to access: ").strip()
        
        print(f"📧 Accessing mailbox for: {user_email}\n")
        
        # Step 3: Get user profile
        print("👤 Fetching user profile...")
        profile_result = await client.call_tool("get_user_profile", {
            "user_email": user_email
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
        
        # Step 4: List emails
        print(f"\n📬 Fetching latest emails for {user_email}...")
        emails_result = await client.call_tool("list_emails", {
            "user_email": user_email,
            "folder": "inbox",
            "limit": 5,
            "include_body": True
        })
        emails = json.loads(emails_result.content[0].text)
        
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
        
        # Step 5: Search emails
        print(f"\n🔍 Searching for emails with 'meeting' in subject...")
        search_result = await client.call_tool("search_emails", {
            "user_email": user_email,
            "query": "meeting",
            "limit": 3
        })
        search_emails = json.loads(search_result.content[0].text)
        
        print(f"Found {len(search_emails)} emails matching 'meeting'")
        for email in search_emails:
            subject = email.get('subject', 'No subject')
            date = email.get('receivedDateTime', '')[:10]
            print(f"  - [{date}] {subject}")
        
        print("\n" + "="*70)
        print("✨ Complete! Key features demonstrated:")
        print("   1. ✅ No user authentication required (app permissions)")
        print("   2. ✅ Listed users in organization")
        print("   3. ✅ Accessed any user's mailbox")
        print("   4. ✅ Retrieved emails with full details")
        print("   5. ✅ Searched emails across mailboxes")
        print("="*70)


if __name__ == "__main__":
    print("Make sure the application-mcp-server is running:")
    print("   python main.py\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
