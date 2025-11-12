"""MCP tools for authentication and Microsoft Graph access"""
import sys
from typing import Any, Optional
from . import auth, graph
from .mcp_instance import mcp


def get_oauth_callback_data():
    """Get the OAuth callback data from the server's callback handler"""
    try:
        from . import server
        return server._callback_store
    except Exception:
        return None


# ============================================================================
# Account Management Tools
# ============================================================================

@mcp.tool
def list_accounts() -> list[dict[str, str]]:
    """
    List all authenticated Microsoft accounts.
    
    Returns:
        List of accounts with username and account_id
    """
    accounts = auth.list_accounts()
    return [{"username": a.username, "account_id": a.account_id} for a in accounts]


@mcp.tool
def authenticate_account() -> dict[str, str]:
    """
    Start OAuth authentication flow for a new account.
    
    Returns:
        Dictionary with auth_url and state for browser authentication
    """
    auth_url, state = auth.authenticate_new_account()

    return {
        "status": "authentication_required",
        "auth_url": auth_url,
        "state": state,
        "message": "Open auth_url in browser, then call check_callback with the state"
    }


@mcp.tool
async def check_callback(state: str) -> dict[str, Any]:
    """
    Check if OAuth callback has been received (non-blocking poll).
    
    Args:
        state: The state parameter from authenticate_account
    
    Returns:
        Dictionary with callback status and auth_code if received
    """
    callback_store = get_oauth_callback_data()
    
    if callback_store and state in callback_store:
        callback_data = callback_store[state]
        
        if callback_data.get("error"):
            return {
                "received": True,
                "success": False,
                "error": callback_data["error"],
                "error_description": callback_data.get("error_description", "")
            }
        
        return {
            "received": True,
            "success": True,
            "auth_code": callback_data["auth_code"]
        }
    
    return {
        "received": False,
        "message": "Callback not yet received"
    }


@mcp.tool
def complete_authentication(auth_code: str) -> dict[str, str]:
    """
    Complete authentication by exchanging authorization code for token.
    
    Args:
        auth_code: Authorization code from OAuth callback
    
    Returns:
        Account information
    """
    print(f"[TOOL] complete_authentication called", file=sys.stderr)
    
    try:
        account = auth.complete_authorization_code_flow(auth_code)
        print(f"[TOOL] Auth flow completed, account: {account}", file=sys.stderr)
    except Exception as e:
        print(f"[TOOL] Error in complete_authorization_code_flow: {e}", file=sys.stderr)
        raise

    if not account:
        raise Exception("Failed to get account information after authentication")

    return {
        "status": "authenticated",
        "username": account.username,
        "account_id": account.account_id,
        "message": f"Successfully authenticated as {account.username}"
    }


@mcp.tool
def logout_account(account_id: str) -> dict[str, str]:
    """
    Logout an account (remove from cache).
    
    Args:
        account_id: Account ID to logout
    
    Returns:
        Success confirmation
    """
    auth.remove_account(account_id)
    return {
        "status": "logged_out",
        "account_id": account_id,
        "message": "Account logged out successfully"
    }


# ============================================================================
# User Profile Tool
# ============================================================================

@mcp.tool
async def get_user_profile(account_id: Optional[str] = None) -> dict[str, Any]:
    """
    Get user profile information from Microsoft Graph.
    
    Args:
        account_id: Account ID (optional, uses first account if not specified)
    
    Returns:
        User profile with displayName, mail, userPrincipalName, etc.
    """
    result = await graph.get_user_profile(account_id)
    
    return {
        "id": result.get("id"),
        "displayName": result.get("displayName"),
        "mail": result.get("mail"),
        "userPrincipalName": result.get("userPrincipalName"),
        "givenName": result.get("givenName"),
        "surname": result.get("surname"),
        "jobTitle": result.get("jobTitle"),
        "officeLocation": result.get("officeLocation"),
        "mobilePhone": result.get("mobilePhone"),
        "businessPhones": result.get("businessPhones", []),
    }


# ============================================================================
# Email Tools
# ============================================================================

@mcp.tool
async def list_emails(
    account_id: str,
    folder: str = "inbox",
    limit: int = 10,
    include_body: bool = True,
) -> list[dict[str, Any]]:
    """
    List emails from specified folder.
    
    Args:
        account_id: Account ID to list emails for
        folder: Folder name (inbox, sent, drafts, deleted, junk)
        limit: Maximum number of emails to return (default 10, max 100)
        include_body: Whether to include email body content
    
    Returns:
        List of email objects with subject, from, to, date, body, etc.
    """
    print(f"[TOOL] list_emails called with account_id={account_id}, folder={folder}, limit={limit}", file=sys.stderr)
    
    try:
        emails = await graph.list_emails(account_id, folder, limit, include_body)
        print(f"[TOOL] Retrieved {len(emails)} emails", file=sys.stderr)
        return emails
    except Exception as e:
        print(f"[TOOL] ERROR in list_emails: {e}", file=sys.stderr)
        raise


@mcp.tool
async def get_email(email_id: str, account_id: Optional[str] = None) -> dict[str, Any]:
    """
    Get specific email by ID.
    
    Args:
        email_id: Email ID
        account_id: Account ID (optional)
    
    Returns:
        Email object with full details
    """
    return await graph.get_email(email_id, account_id)


@mcp.tool
async def search_emails(
    query: str,
    account_id: Optional[str] = None,
    limit: int = 10
) -> list[dict[str, Any]]:
    """
    Search for emails.
    
    Args:
        query: Search query
        account_id: Account ID (optional)
        limit: Maximum results
    
    Returns:
        List of matching emails
    """
    return await graph.search_emails(query, account_id, limit)
