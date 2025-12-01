"""
Test authentication and diagnose 401 errors
Run this to check your Azure configuration
"""
import os
import sys
import jwt
import json
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.application_mcp import auth

load_dotenv()


def decode_token(token: str):
    """Decode JWT token without verification to inspect claims"""
    try:
        # Decode without verification to see what's in the token
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        return {"error": str(e)}


def main():
    print("="*70)
    print("🔍 Azure Application Permissions - Diagnostic Tool")
    print("="*70)
    print()
    
    # Check environment variables
    print("📋 Step 1: Checking environment variables...")
    print("-"*70)
    
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    
    print(f"AZURE_CLIENT_ID: {'✅ Set' if client_id else '❌ Missing'}")
    if client_id:
        print(f"  Value: {client_id[:8]}...{client_id[-4:]}")
    
    print(f"AZURE_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Missing'}")
    if client_secret:
        print(f"  Value: {client_secret[:4]}...{client_secret[-4:]}")
    
    print(f"AZURE_TENANT_ID: {'✅ Set' if tenant_id else '❌ Missing'}")
    if tenant_id:
        print(f"  Value: {tenant_id}")
        if tenant_id in ['common', 'consumers', 'organizations']:
            print(f"  ⚠️  WARNING: '{tenant_id}' won't work with application permissions!")
            print(f"      You must use your organization's specific tenant ID")
    print()
    
    if not all([client_id, client_secret, tenant_id]):
        print("❌ Missing required environment variables!")
        print("   Please check your .env file")
        return
    
    # Try to get token
    print("📋 Step 2: Attempting to acquire token...")
    print("-"*70)
    
    try:
        token = auth.get_token()
        print("✅ Token acquired successfully!")
        print()
        
        # Decode and analyze token
        print("📋 Step 3: Analyzing token claims...")
        print("-"*70)
        
        claims = decode_token(token)
        
        print("\n🔑 Token Information:")
        print(f"  App ID (appid): {claims.get('appid', 'N/A')}")
        print(f"  Tenant ID (tid): {claims.get('tid', 'N/A')}")
        print(f"  Audience (aud): {claims.get('aud', 'N/A')}")
        print(f"  Issuer (iss): {claims.get('iss', 'N/A')}")
        
        # Check roles (application permissions)
        roles = claims.get('roles', [])
        print(f"\n📜 Application Permissions (roles) in token:")
        if roles:
            for role in roles:
                print(f"  ✅ {role}")
        else:
            print("  ❌ NO ROLES FOUND!")
            print("     This means application permissions are not granted/consented")
        
        # Check if required permissions are present
        print(f"\n🔍 Checking required permissions:")
        required_permissions = ['Mail.Read', 'User.Read.All']
        
        missing_permissions = []
        for perm in required_permissions:
            if perm in roles:
                print(f"  ✅ {perm}")
            else:
                print(f"  ❌ {perm} - MISSING!")
                missing_permissions.append(perm)
        
        print()
        
        if not roles:
            print("="*70)
            print("❌ PROBLEM IDENTIFIED: No application permissions in token!")
            print("="*70)
            print("\n🔧 How to fix:")
            print("1. Go to Azure Portal > App Registrations > Your App")
            print("2. Go to 'API permissions'")
            print("3. Remove any DELEGATED permissions (if present)")
            print("4. Click 'Add a permission' > Microsoft Graph > 'Application permissions' (NOT Delegated)")
            print("5. Add these APPLICATION permissions:")
            print("   - Mail.Read (Application)")
            print("   - User.Read.All (Application)")
            print("6. Click 'Grant admin consent for [Your Organization]' ✅")
            print("7. Wait 5-10 minutes for changes to propagate")
            print()
            print("⚠️  IMPORTANT: Make sure you select 'Application permissions', not 'Delegated permissions'!")
            print()
        elif missing_permissions:
            print("="*70)
            print("⚠️  PROBLEM: Some required permissions are missing!")
            print("="*70)
            print("\n🔧 How to fix:")
            print("1. Go to Azure Portal > App Registrations > Your App")
            print("2. Go to 'API permissions'")
            print("3. Click 'Add a permission' > Microsoft Graph > 'Application permissions'")
            for perm in missing_permissions:
                print(f"4. Add '{perm}' as APPLICATION permission (not delegated)")
            print("5. Click 'Grant admin consent for [Your Organization]' ✅")
            print("6. Wait 5-10 minutes for changes to propagate")
            print()
            print("⚠️  CRITICAL: Accessing mailboxes requires 'Mail.Read' APPLICATION permission!")
            print()
        else:
            print("="*70)
            print("✅ All required permissions are present in token!")
            print("="*70)
            print("\nIf you're still getting 401 errors:")
            print("1. Wait a few minutes (permission propagation can take time)")
            print("2. Clear token cache: auth.clear_token_cache()")
            print("3. Check that you're using the correct tenant ID")
            print("4. Verify the user email exists in your organization")
            print()
        
        # Show full token for debugging
        print("\n📄 Full token claims (for advanced debugging):")
        print(json.dumps(claims, indent=2))
        
    except Exception as e:
        print(f"❌ Failed to acquire token!")
        print(f"   Error: {e}")
        print()
        print("🔧 Common causes:")
        print("1. Invalid client secret (expired or incorrect)")
        print("2. Wrong tenant ID")
        print("3. Application doesn't exist or was deleted")
        print("4. Network/firewall issues")
        print()


if __name__ == "__main__":
    main()
