"""Authentication using Client Credentials flow with Application permissions"""
import os
import threading
import msal
from typing import Optional
from dotenv import load_dotenv
from .config import config
from .logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

# Thread-safe token cache with threading lock
_cached_token: Optional[dict] = None
_token_lock = threading.Lock()


def get_app() -> msal.ConfidentialClientApplication:
    """
    Get MSAL application instance for Client Credentials flow.
    No user interaction required - app authenticates with its own credentials.
    """
    client_id = config.AZURE_CLIENT_ID
    if not client_id:
        raise ValueError("AZURE_CLIENT_ID environment variable is required")

    client_secret = config.AZURE_CLIENT_SECRET
    if not client_secret:
        raise ValueError("AZURE_CLIENT_SECRET environment variable is required")

    tenant_id = config.AZURE_TENANT_ID
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
    
    Thread-safe implementation with token caching.
    This flow is for server-to-server scenarios where the app acts on its own behalf,
    not on behalf of a user. No user interaction is required.
    
    Returns:
        Access token string
    
    Raises:
        Exception: If token acquisition fails
    """
    global _cached_token
    
    with _token_lock:
        app = get_app()
        
        # Scope for Microsoft Graph with application permissions
        # Use .default scope which requests all static permissions configured in Azure portal
        scopes = ["https://graph.microsoft.com/.default"]
        
        logger.debug("Acquiring token with Client Credentials flow")
        
        # Try to get token silently from cache first
        result = app.acquire_token_silent(scopes, account=None)
        
        if not result:
            # No cached token or expired, acquire new token using client credentials
            logger.info("No cached token, acquiring new token from Azure AD")
            result = app.acquire_token_for_client(scopes=scopes)
        else:
            logger.debug("Using cached token")
        
        if "access_token" in result:
            _cached_token = result
            logger.debug("Token acquired successfully")
            return result["access_token"]
        
        # Token acquisition failed
        error = result.get("error", "unknown_error")
        error_description = result.get("error_description", "No description available")
        
        logger.error(
            "Failed to acquire token",
            extra={
                "error": error,
                "error_description": error_description,
            }
        )
        
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
