"""Authentication using Client Credentials flow with Application permissions"""
import os
import sys
import msal
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# In-memory token cache (single token for the application)
_cached_token: Optional[dict] = None


def get_app() -> msal.ConfidentialClientApplication:
    """
    Get MSAL application instance for Client Credentials flow.
    No user interaction required - app authenticates with its own credentials.
    """
    client_id = os.getenv("AZURE_CLIENT_ID")
    if not client_id:
        raise ValueError("AZURE_CLIENT_ID environment variable is required")

    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    if not client_secret:
        raise ValueError("AZURE_CLIENT_SECRET environment variable is required")

    tenant_id = os.getenv("AZURE_TENANT_ID")
    if not tenant_id:
        raise ValueError(
            "AZURE_TENANT_ID environment variable is required. "
            "For application permissions, you must specify your organization's tenant ID "
            "(cannot use 'common' or 'consumers')"
        )

    authority = f"https://login.microsoftonline.com/{tenant_id}"

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )

    return app


def get_token() -> str:
    """
    Get access token using Client Credentials flow (Application permissions).
    
    This flow is for server-to-server scenarios where the app acts on its own behalf,
    not on behalf of a user. No user interaction is required.
    
    Returns:
        Access token string
    
    Raises:
        Exception: If token acquisition fails
    """
    global _cached_token
    
    app = get_app()
    
    # Scope for Microsoft Graph with application permissions
    # Use .default scope which requests all static permissions configured in Azure portal
    scopes = ["https://graph.microsoft.com/.default"]
    
    print(f"[DEBUG AUTH] Acquiring token with Client Credentials flow", file=sys.stderr)
    print(f"[DEBUG AUTH] Scopes: {scopes}", file=sys.stderr)
    
    # Try to get token silently from cache first
    result = app.acquire_token_silent(scopes, account=None)
    
    if not result:
        # No cached token or expired, acquire new token using client credentials
        print(f"[DEBUG AUTH] No cached token, acquiring new token...", file=sys.stderr)
        result = app.acquire_token_for_client(scopes=scopes)
    else:
        print(f"[DEBUG AUTH] Using cached token", file=sys.stderr)
    
    if "access_token" in result:
        _cached_token = result
        print(f"[DEBUG AUTH] Token acquired successfully", file=sys.stderr)
        return result["access_token"]
    
    # Token acquisition failed
    error = result.get("error", "unknown_error")
    error_description = result.get("error_description", "No description available")
    
    print(f"[DEBUG AUTH] Error: {error}", file=sys.stderr)
    print(f"[DEBUG AUTH] Description: {error_description}", file=sys.stderr)
    
    raise Exception(
        f"Failed to acquire token: {error} - {error_description}\n"
        f"Make sure:\n"
        f"1. Application permissions (not delegated) are configured in Azure Portal\n"
        f"2. Admin consent has been granted for the permissions\n"
        f"3. AZURE_TENANT_ID is set to your organization's tenant ID"
    )


def clear_token_cache() -> None:
    """Clear the cached token (useful for testing or forcing refresh)"""
    global _cached_token
    _cached_token = None
    print(f"[DEBUG AUTH] Token cache cleared", file=sys.stderr)
