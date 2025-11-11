"""Minimal MCP tools for email reading and user profile only"""
import sys
import os
from typing import Any
from . import auth, graph
from .mcp_instance import mcp


def get_oauth_callback_data():
    """Get the OAuth callback data from the server's callback handler"""
    try:
        from . import server
        return server._callback_data
    except Exception:
        return None


# Account management tools
@mcp.tool
def list_accounts() -> list[dict[str, str]]:
    """List all authenticated Microsoft accounts"""
    accounts = auth.list_accounts()
    return [{"username": a.username, "account_id": a.account_id} for a in accounts]


@mcp.tool
def authenticate_account() -> dict[str, str]:
    """Authenticate a new Microsoft account using authorization code flow

    Returns authentication URL for the user to visit and authenticate.
    The callback will be automatically captured by the server.
    After the user authenticates in browser, use 'wait_for_callback' tool with the returned state.
    """
    # Reset callback data
    callback_data = get_oauth_callback_data()
    if callback_data:
        callback_data["ready"].clear()
        callback_data["auth_code"] = None
        callback_data["state"] = None
        callback_data["error"] = None
    
    auth_url, state = auth.authenticate_new_account()

    return {
        "status": "authentication_required",
        "auth_url": auth_url,
        "state": state,
        "message": "Open this URL in your browser to authenticate, then call 'wait_for_callback' with the state parameter"
    }


@mcp.tool
def wait_for_callback(timeout: int = 300, state: str = None) -> dict[str, Any]:
    """Wait for OAuth callback from the browser redirect
    
    Supports two modes:
    1. Built-in callback server (default for local development)
    2. External callback API (for Kubernetes/production)

    Args:
        timeout: Maximum seconds to wait for callback (default 300 = 5 minutes)
        state: OAuth state parameter from authenticate_account (required for external callback API)

    Returns:
        Callback data with auth_code and state if successful
    """
    import httpx
    import time
    
    # Check if using external callback API
    callback_api_url = auth.OAUTH_CALLBACK_API_URL
    
    if callback_api_url and state:
        # Mode 2: Poll external callback API
        print(f"[TOOL] Using external callback API: {callback_api_url}", file=sys.stderr)
        
        api_url = callback_api_url.replace('{state}', state)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = httpx.get(api_url, timeout=5.0)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('error'):
                        return {
                            "status": "error",
                            "error": data['error'],
                            "error_description": data.get('error_description')
                        }
                    return {
                        "status": "success",
                        "auth_code": data['auth_code'],
                        "state": data['state']
                    }
                elif response.status_code == 404:
                    # Callback not received yet, wait and retry
                    time.sleep(2)
                    continue
                elif response.status_code == 410:
                    return {
                        "status": "error",
                        "error": "Callback already retrieved"
                    }
                else:
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"[TOOL] Error polling callback API: {e}", file=sys.stderr)
                time.sleep(2)
                continue
        
        return {
            "status": "timeout",
            "error": f"No callback received within {timeout} seconds"
        }
    
    else:
        # Mode 1: Use built-in callback server
        callback_data = get_oauth_callback_data()
        if not callback_data:
            return {
                "status": "error",
                "error": "OAuth callback server not available. Set MICROSOFT_MCP_OAUTH_CALLBACK_API_URL to use external callback service."
            }
        
        # Wait for callback
        if callback_data["ready"].wait(timeout=timeout):
            if callback_data["error"]:
                return {
                    "status": "error",
                    "error": callback_data["error"]
                }
            
            return {
                "status": "success",
                "auth_code": callback_data["auth_code"],
                "state": callback_data["state"]
            }
        else:
            return {
                "status": "timeout",
            "error": f"No callback received within {timeout} seconds"
        }


@mcp.tool
def complete_authentication(auth_code: str, state: str) -> dict[str, str]:
    """Complete the authentication process with the authorization code from the redirect

    Args:
        auth_code: The authorization code from the redirect URL (the 'code' parameter)
        state: The state parameter from the redirect URL (for CSRF protection)

    Returns:
        Account information if authentication was successful
    """
    print(f"[TOOL] complete_authentication called", file=sys.stderr)
    print(f"[TOOL] auth_code length: {len(auth_code)}", file=sys.stderr)
    print(f"[TOOL] state length: {len(state)}", file=sys.stderr)
    
    try:
        account = auth.complete_authorization_code_flow(auth_code, state)
        print(f"[TOOL] Auth flow completed, account: {account}", file=sys.stderr)
    except Exception as e:
        print(f"[TOOL] Error in complete_authorization_code_flow: {e}", file=sys.stderr)
        raise

    if not account:
        raise Exception("Failed to get account information after authentication")

    # Verify the cache was written
    if os.path.exists(auth.CACHE_FILE):
        print(f"✅ Token cache saved to {auth.CACHE_FILE}", file=sys.stderr)
    else:
        print(f"⚠️  Warning: Token cache file not found at {auth.CACHE_FILE}", file=sys.stderr)

    return {
        "status": "success",
        "message": "Authentication completed successfully",
        "username": account.username,
        "account_id": account.account_id,
    }


# User profile tool
@mcp.tool
def get_user_profile(account_id: str) -> dict[str, Any]:
    """Get the current user's profile information
    
    Args:
        account_id: The account ID to get profile for
        
    Returns:
        User profile information including displayName, mail, userPrincipalName, etc.
    """
    result = graph.request("GET", "/me", account_id)
    if not result:
        raise ValueError("Failed to get user profile")
    
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


# Email tools
@mcp.tool
def list_emails(
    account_id: str,
    folder: str = "inbox",
    limit: int = 10,
    include_body: bool = True,
) -> list[dict[str, Any]]:
    """List emails from specified folder
    
    Args:
        account_id: The account ID to list emails for
        folder: Folder name (inbox, sent, drafts, deleted, junk)
        limit: Maximum number of emails to return (default 10, max 100)
        include_body: Whether to include email body content (default True)
    
    Returns:
        List of email objects with subject, from, to, date, body, etc.
    """
    import sys
    print(f"[TOOL] list_emails called with account_id={account_id}, folder={folder}, limit={limit}", file=sys.stderr)
    
    FOLDERS = {
        "inbox": "inbox",
        "sent": "sentitems",
        "drafts": "drafts",
        "deleted": "deleteditems",
        "junk": "junkemail",
    }
    
    folder_path = FOLDERS.get(folder.casefold(), folder)
    print(f"[TOOL] Resolved folder_path: {folder_path}", file=sys.stderr)

    if include_body:
        select_fields = "id,subject,from,toRecipients,ccRecipients,receivedDateTime,hasAttachments,body,conversationId,isRead"
    else:
        select_fields = "id,subject,from,toRecipients,receivedDateTime,hasAttachments,conversationId,isRead"

    params = {
        "$top": min(limit, 100),
        "$select": select_fields,
        "$orderby": "receivedDateTime desc",
    }
    
    print(f"[TOOL] Making paginated request to /me/mailFolders/{folder_path}/messages", file=sys.stderr)

    try:
        emails = list(
            graph.request_paginated(
                f"/me/mailFolders/{folder_path}/messages",
                account_id,
                params=params,
                limit=limit,
            )
        )
        print(f"[TOOL] Retrieved {len(emails)} emails", file=sys.stderr)
        return emails
    except Exception as e:
        print(f"[TOOL] ERROR in list_emails: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


@mcp.tool
def get_email(
    email_id: str,
    account_id: str,
    include_body: bool = True,
    body_max_length: int = 50000,
) -> dict[str, Any]:
    """Get detailed information about a specific email

    Args:
        email_id: The email ID to retrieve
        account_id: The account ID
        include_body: Whether to include the email body (default: True)
        body_max_length: Maximum characters for body content (default: 50000)
    
    Returns:
        Email object with full details
    """
    result = graph.request("GET", f"/me/messages/{email_id}", account_id)
    if not result:
        raise ValueError(f"Email with ID {email_id} not found")

    # Truncate body if needed
    if include_body and "body" in result and "content" in result["body"]:
        content = result["body"]["content"]
        if len(content) > body_max_length:
            result["body"]["content"] = content[:body_max_length] + "\n\n[Content truncated...]"

    return result


@mcp.tool
def search_emails(
    account_id: str,
    query: str,
    limit: int = 10,
    include_body: bool = False,
) -> list[dict[str, Any]]:
    """Search emails by subject, from, or content
    
    Args:
        account_id: The account ID to search emails for
        query: Search query string (searches subject, from, body)
        limit: Maximum number of results (default 10, max 100)
        include_body: Whether to include email body (default False)
    
    Returns:
        List of matching email objects
    """
    if include_body:
        select_fields = "id,subject,from,toRecipients,receivedDateTime,hasAttachments,body,isRead"
    else:
        select_fields = "id,subject,from,toRecipients,receivedDateTime,hasAttachments,isRead"

    params = {
        "$search": f'"{query}"',
        "$top": min(limit, 100),
        "$select": select_fields,
        "$orderby": "receivedDateTime desc",
    }

    emails = list(
        graph.request_paginated(
            "/me/messages",
            account_id,
            params=params,
            limit=limit,
        )
    )

    return emails
