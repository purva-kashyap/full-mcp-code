"""OAuth authentication handling with MSAL and in-memory token caching"""
import os
import sys
import msal
import secrets
from typing import NamedTuple, Optional
from dotenv import load_dotenv

load_dotenv()

# In-memory cache storage
_in_memory_cache: Optional[str] = None

# Microsoft Graph scopes (use short-form, not full URLs)
SCOPES = [
    "User.Read",
    "Mail.Read",
]

# Redirect URI for OAuth callback
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback")


class Account(NamedTuple):
    username: str
    account_id: str


def _read_cache() -> Optional[str]:
    """Read token cache from memory"""
    return _in_memory_cache


def _write_cache(content: str) -> None:
    """Write token cache to memory"""
    global _in_memory_cache
    _in_memory_cache = content


def get_app() -> msal.ConfidentialClientApplication:
    """Get MSAL application instance with token cache"""
    client_id = os.getenv("AZURE_CLIENT_ID")
    if not client_id:
        raise ValueError("AZURE_CLIENT_ID environment variable is required")

    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    if not client_secret:
        raise ValueError("AZURE_CLIENT_SECRET environment variable is required")

    tenant_id = os.getenv("AZURE_TENANT_ID", "consumers")
    authority = f"https://login.microsoftonline.com/{tenant_id}"

    # Load existing cache
    cache = msal.SerializableTokenCache()
    cache_content = _read_cache()
    if cache_content:
        cache.deserialize(cache_content)

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
        token_cache=cache
    )

    return app


def get_token(account_id: Optional[str] = None) -> str:
    """
    Get access token for account (uses cache, auto-refreshes).
    
    Args:
        account_id: Account ID to get token for. If None, uses first account.
    
    Returns:
        Access token string
    
    Raises:
        Exception: If no account found or token acquisition fails
    """
    app = get_app()
    accounts = app.get_accounts()
    
    account = None
    if account_id:
        account = next(
            (a for a in accounts if a["home_account_id"] == account_id), None
        )
        if not account:
            raise Exception(
                f"Account with ID {account_id} not found. Please authenticate first."
            )
    elif accounts:
        account = accounts[0]
    else:
        raise Exception(
            "No authenticated accounts found. Please authenticate first."
        )

    print(f"[DEBUG] Getting token for account: {account.get('username')}", file=sys.stderr)
    
    # Try to get token silently (from cache or using refresh token)
    result = app.acquire_token_silent(SCOPES, account=account)
    
    if not result:
        raise Exception(
            f"Failed to acquire token for account {account.get('username', 'unknown')}. "
            "The token may have expired. Please re-authenticate."
        )

    if "error" in result:
        raise Exception(
            f"Auth failed: {result.get('error_description', result['error'])}"
        )

    # Save cache if it changed
    cache = app.token_cache
    if isinstance(cache, msal.SerializableTokenCache) and cache.has_state_changed:
        _write_cache(cache.serialize())

    return result["access_token"]


def list_accounts() -> list[Account]:
    """List all authenticated accounts"""
    app = get_app()
    return [
        Account(username=a["username"], account_id=a["home_account_id"])
        for a in app.get_accounts()
    ]


def authenticate_new_account() -> tuple[str, str]:
    """
    Initiate authorization code flow.
    
    Returns:
        Tuple of (auth_url, state)
    """
    app = get_app()
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    print(f"[DEBUG AUTH] SCOPES: {SCOPES}", file=sys.stderr)
    print(f"[DEBUG AUTH] REDIRECT_URI: {REDIRECT_URI}", file=sys.stderr)
    
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state
    )
    
    print(f"[DEBUG AUTH] Auth URL: {auth_url[:200]}...", file=sys.stderr)
    
    return auth_url, state


def complete_authorization_code_flow(auth_code: str) -> Optional[Account]:
    """
    Complete the authorization code flow with the code from redirect.
    
    Args:
        auth_code: The authorization code from the redirect URL
        
    Returns:
        Account information if successful
    """
    app = get_app()
    
    print(f"[DEBUG AUTH] Completing auth code flow...", file=sys.stderr)
    
    result = app.acquire_token_by_authorization_code(
        code=auth_code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    if "error" in result:
        print(f"[DEBUG AUTH] Error: {result.get('error')}", file=sys.stderr)
        raise Exception(
            f"Auth failed: {result.get('error_description', result['error'])}"
        )
    
    # Save cache
    cache = app.token_cache
    if isinstance(cache, msal.SerializableTokenCache):
        _write_cache(cache.serialize())
    
    # Get the newly added account
    accounts = app.get_accounts()
    if accounts:
        # Find the account that matches the token we just got
        for account in accounts:
            if (
                account.get("username", "").lower()
                == result.get("id_token_claims", {})
                .get("preferred_username", "")
                .lower()
            ):
                return Account(
                    username=account["username"], account_id=account["home_account_id"]
                )
        # If exact match not found, return the last account
        account = accounts[-1]
        return Account(
            username=account["username"], account_id=account["home_account_id"]
        )
    
    return None


def remove_account(account_id: str) -> None:
    """Remove account from cache (logout)"""
    app = get_app()
    accounts = app.get_accounts()
    
    account = next(
        (a for a in accounts if a["home_account_id"] == account_id), None
    )
    
    if account:
        app.remove_account(account)
        
        # Save cache
        cache = app.token_cache
        if isinstance(cache, msal.SerializableTokenCache):
            _write_cache(cache.serialize())
