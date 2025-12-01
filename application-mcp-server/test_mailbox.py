"""
Clear token cache and test mailbox access
"""
import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.application_mcp import auth, graph


async def main():
    print("="*70)
    print("🔧 Clearing token cache and testing mailbox access")
    print("="*70)
    print()
    
    # Clear cache
    print("1️⃣  Clearing token cache...")
    auth.clear_token_cache()
    print("   ✅ Cache cleared")
    print()
    
    # Get fresh token
    print("2️⃣  Acquiring fresh token...")
    try:
        token = auth.get_token()
        print("   ✅ Fresh token acquired")
        print()
    except Exception as e:
        print(f"   ❌ Failed to get token: {e}")
        return
    
    # Test user listing
    print("3️⃣  Testing user listing...")
    try:
        users = await graph.list_users(limit=5)
        print(f"   ✅ Found {len(users)} users")
        
        org_users = [u for u in users if '#EXT#' not in u.get('userPrincipalName', '')]
        if org_users:
            print(f"   ✅ Found {len(org_users)} organization users")
            test_user = org_users[0]
        else:
            print("   ⚠️  No organization users found, using first user")
            test_user = users[0]
        
        upn = test_user.get('userPrincipalName', 'unknown')
        display_name = test_user.get('displayName', 'Unknown')
        print(f"   📧 Test user: {display_name} ({upn})")
        print()
        
        # Test mailbox access
        print("4️⃣  Testing mailbox access...")
        print(f"   Attempting to read emails for: {upn}")
        
        try:
            emails = await graph.list_emails(
                user_email=upn,
                folder="inbox",
                limit=1,
                include_body=False
            )
            print(f"   ✅ SUCCESS! Retrieved {len(emails)} email(s)")
            
            if emails:
                email = emails[0]
                subject = email.get('subject', 'No subject')
                date = email.get('receivedDateTime', '')[:10]
                print(f"   📧 Latest email: [{date}] {subject}")
            else:
                print("   📭 Mailbox is empty")
            
            print()
            print("="*70)
            print("✅ All tests passed! Your application can access mailboxes.")
            print("="*70)
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Failed to access mailbox: {error_msg}")
            print()
            
            if '401' in error_msg:
                print("="*70)
                print("❌ Still getting 401 error")
                print("="*70)
                print()
                print("Possible causes:")
                print("1. Permission propagation delay (wait 5-10 more minutes)")
                print("2. User doesn't have an Exchange Online mailbox")
                print("3. Application registration issue")
                print()
                print("Try these steps:")
                print("1. Wait 10 minutes and run this script again")
                print("2. Verify the user has an Exchange Online license")
                print("3. Check Azure Portal > App Registrations > Your App > API permissions")
                print("   - Mail.Read should show 'Application' type")
                print("   - Should have green checkmark for admin consent")
                print()
            elif '404' in error_msg:
                print("="*70)
                print("❌ 404 Error - User or mailbox not found")
                print("="*70)
                print()
                print("This means:")
                print(f"- User '{upn}' exists but doesn't have a mailbox")
                print("- User might be external/guest without Exchange license")
                print()
                print("Solution:")
                print("- Test with a different user who has an Exchange Online mailbox")
                print("- Assign Exchange Online license to this user")
                print()
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
