"""
Check if a user has a mailbox configured
"""
import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.application_mcp import auth, graph


async def check_user_mailbox(user_email: str):
    """Check if user has a mailbox"""
    print(f"\n🔍 Checking mailbox for: {user_email}")
    print("-" * 70)
    
    try:
        # Try to get mailbox settings
        result = await graph.request(
            "GET",
            f"/users/{user_email}/mailboxSettings"
        )
        print("✅ User HAS a mailbox!")
        print(f"   Timezone: {result.get('timeZone', 'N/A')}")
        print(f"   Language: {result.get('language', {}).get('displayName', 'N/A')}")
        return True
    except Exception as e:
        error_msg = str(e)
        if '404' in error_msg or 'MailboxNotEnabledForRESTAPI' in error_msg:
            print("❌ User does NOT have a mailbox")
            print("   This user hasn't been assigned an Exchange Online license")
            return False
        else:
            print(f"❓ Unclear: {error_msg}")
            return None


async def main():
    print("="*70)
    print("📫 Mailbox Configuration Checker")
    print("="*70)
    
    # Clear cache and get fresh token
    auth.clear_token_cache()
    
    # Get all users
    print("\n1️⃣  Fetching users...")
    users = await graph.list_users(limit=10)
    
    org_users = [u for u in users if '#EXT#' not in u.get('userPrincipalName', '')]
    
    print(f"   Found {len(org_users)} organization users")
    print()
    
    if not org_users:
        print("❌ No organization users found")
        return
    
    # Check each user for mailbox
    print("2️⃣  Checking which users have mailboxes...")
    print("="*70)
    
    users_with_mailbox = []
    users_without_mailbox = []
    
    for user in org_users:
        upn = user.get('userPrincipalName', '')
        display_name = user.get('displayName', 'Unknown')
        
        print(f"\n👤 {display_name}")
        print(f"   UPN: {upn}")
        
        has_mailbox = await check_user_mailbox(upn)
        
        if has_mailbox:
            users_with_mailbox.append((display_name, upn))
        elif has_mailbox is False:
            users_without_mailbox.append((display_name, upn))
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    if users_with_mailbox:
        print(f"\n✅ Users WITH mailboxes ({len(users_with_mailbox)}):")
        for name, upn in users_with_mailbox:
            print(f"   • {name} ({upn})")
        
        print("\n💡 You can test with any of these users in client_example.py")
    else:
        print("\n❌ NO users with mailboxes found!")
        print("\n🔧 To fix this:")
        print("1. Go to Microsoft 365 Admin Center")
        print("2. Assign an Exchange Online license to at least one user")
        print("3. Wait 5-10 minutes for mailbox provisioning")
        print("4. Run this script again")
    
    if users_without_mailbox:
        print(f"\n⚠️  Users WITHOUT mailboxes ({len(users_without_mailbox)}):")
        for name, upn in users_without_mailbox:
            print(f"   • {name} ({upn})")
        print("\n   These users need Exchange Online licenses to have mailboxes")


if __name__ == "__main__":
    asyncio.run(main())
