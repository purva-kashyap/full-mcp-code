import os
import sys
import msal
import pathlib as pl
from typing import NamedTuple
from dotenv import load_dotenv
import secrets

load_dotenv()

CACHE_FILE = pl.Path.home() / ".microsoft_mcp_token_cache.json"

# Explicitly request the scopes we need
# Using specific scopes instead of .default for better compatibility
SCOPES = [
    "https://graph.microsoft.com/User.Read",
    "https://graph.microsoft.com/Mail.Read",
]

# Redirect URI for authorization code flow - must match Azure AD app registration
# Can be configured via environment variable for different deployment scenarios
# Examples:
#   - Local development: http://localhost:8000/callback
#   - Kubernetes: https://yourdomain.com/oauth/callback
#   - Separate service: http://oauth-callback-service:8000/callback
REDIRECT_URI = os.getenv("MICROSOFT_MCP_REDIRECT_URI", "http://localhost:8000/callback")

# Optional: External OAuth callback service URL for retrieving callback data
# If set, the server will poll this URL instead of using built-in callback handler
# Example: http://oauth-callback-service:8000/api/callback/{state}
OAUTH_CALLBACK_API_URL = os.getenv("MICROSOFT_MCP_OAUTH_CALLBACK_API_URL", None)


class Account(NamedTuple):
    username: str
    account_id: str


def _read_cache() -> str | None:
    try:
        return CACHE_FILE.read_text()
    except FileNotFoundError:
        return None


def _write_cache(content: str) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(content)


def get_app() -> msal.ConfidentialClientApplication | msal.PublicClientApplication:
    client_id = os.getenv("MICROSOFT_MCP_CLIENT_ID")
    if not client_id:
        raise ValueError("MICROSOFT_MCP_CLIENT_ID environment variable is required")

    # Check if we have a client secret (Confidential Client) or not (Public Client)
    client_secret = os.getenv("MICROSOFT_MCP_CLIENT_SECRET")

    # For personal Microsoft accounts (like @gmail.com, @outlook.com): use "consumers"
    # For work/school accounts: use "organizations" or specific tenant ID
    # For both: use "common"
    tenant_id = "common"
    authority = f"https://login.microsoftonline.com/{tenant_id}"

    cache = msal.SerializableTokenCache()
    cache_content = _read_cache()
    if cache_content:
        cache.deserialize(cache_content)

    if client_secret:
        # Use ConfidentialClientApplication for server-side apps with client secret
        app = msal.ConfidentialClientApplication(
            client_id, 
            authority=authority, 
            client_credential=client_secret,
            token_cache=cache
        )
    else:
        # Use PublicClientApplication for apps without client secret (with PKCE)
        app = msal.PublicClientApplication(
            client_id, authority=authority, token_cache=cache
        )

    return app


def get_token(account_id: str | None = None) -> str:
    app = get_app()

    accounts = app.get_accounts()
    account = None

    if account_id:
        account = next(
            (a for a in accounts if a["home_account_id"] == account_id), None
        )
        if not account:
            raise Exception(
                f"Account with ID {account_id} not found. Please authenticate first using the authenticate_account tool."
            )
    elif accounts:
        account = accounts[0]
    else:
        raise Exception(
            "No authenticated accounts found. Please authenticate first using the authenticate_account tool."
        )

    print(f"[DEBUG] Requesting token with scopes: {SCOPES}", file=sys.stderr)
    print(f"[DEBUG] Account details: {account}", file=sys.stderr)
    result = app.acquire_token_silent(SCOPES, account=account)
    print(f"[DEBUG] Token result: {result is not None}, has error: {'error' in result if result else 'N/A'}", file=sys.stderr)
    
    if result:
        print(f"[DEBUG] Token result keys: {list(result.keys())}", file=sys.stderr)
        if 'access_token' in result:
            print(f"[DEBUG] Access token obtained (length: {len(result['access_token'])})", file=sys.stderr)
        if 'scopes' in result:
            print(f"[DEBUG] Token scopes: {result.get('scopes')}", file=sys.stderr)

    if not result:
        # Token acquisition failed - need to re-authenticate
        # Don't start an interactive flow here - raise an error instead
        raise Exception(
            f"Failed to acquire token for account {account.get('username', 'unknown')}. "
            "The token may have expired. Please re-authenticate using the authenticate_account tool."
        )

    if "error" in result:
        raise Exception(
            f"Auth failed: {result.get('error_description', result['error'])}"
        )

    cache = app.token_cache
    if isinstance(cache, msal.SerializableTokenCache) and cache.has_state_changed:
        _write_cache(cache.serialize())

    return result["access_token"]


def list_accounts() -> list[Account]:
    app = get_app()
    return [
        Account(username=a["username"], account_id=a["home_account_id"])
        for a in app.get_accounts()
    ]


def authenticate_new_account() -> tuple[str, str]:
    """Initiate authorization code flow
    
    Returns:
        Tuple of (auth_url, state)
    """
    app = get_app()
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state
    )
    
    return auth_url, state


def complete_authorization_code_flow(auth_code: str, state: str) -> Account | None:
    """Complete the authorization code flow with the code from redirect
    
    Args:
        auth_code: The authorization code from the redirect URL
        state: The state parameter to verify (CSRF protection)
        
    Returns:
        Account information if successful
    """
    app = get_app()
    
    print(f"[DEBUG AUTH] Completing auth code flow...", file=sys.stderr)
    print(f"[DEBUG AUTH] Auth code: {auth_code[:20]}...", file=sys.stderr)
    print(f"[DEBUG AUTH] Redirect URI: {REDIRECT_URI}", file=sys.stderr)
    print(f"[DEBUG AUTH] Scopes: {SCOPES}", file=sys.stderr)
    
    result = app.acquire_token_by_authorization_code(
        code=auth_code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    print(f"[DEBUG AUTH] Result keys: {list(result.keys())}", file=sys.stderr)
    
    if 'access_token' in result:
        print(f"[DEBUG AUTH] Access token obtained (length: {len(result['access_token'])})", file=sys.stderr)
    if 'scope' in result:
        print(f"[DEBUG AUTH] Granted scopes: {result.get('scope')}", file=sys.stderr)
    if 'id_token_claims' in result:
        claims = result.get('id_token_claims', {})
        print(f"[DEBUG AUTH] User: {claims.get('preferred_username')}", file=sys.stderr)
    
    if "error" in result:
        print(f"[DEBUG AUTH] Error: {result.get('error')}", file=sys.stderr)
        print(f"[DEBUG AUTH] Error description: {result.get('error_description')}", file=sys.stderr)
        raise Exception(
            f"Auth failed: {result.get('error_description', result['error'])}"
        )
    
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
