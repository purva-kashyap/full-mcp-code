"""Microsoft Graph API client"""
import sys
import httpx
from typing import Any, Optional
from . import auth


async def request(
    method: str,
    endpoint: str,
    account_id: Optional[str] = None,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> Any:
    """
    Make a request to Microsoft Graph API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., "/me" or "/me/messages")
        account_id: Account ID to use for authentication
        params: Query parameters
        json_data: JSON body data
    
    Returns:
        Response JSON data
    """
    token = auth.get_token(account_id)
    
    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    print(f"[GRAPH] {method} {endpoint}", file=sys.stderr)
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=30.0
        )
        
        if response.status_code >= 400:
            print(f"[GRAPH] Error {response.status_code}: {response.text}", file=sys.stderr)
            response.raise_for_status()
        
        return response.json()


async def get_user_profile(account_id: Optional[str] = None) -> dict:
    """Get user profile information"""
    return await request("GET", "/me", account_id)


async def list_emails(
    account_id: Optional[str] = None,
    folder: str = "inbox",
    limit: int = 10,
    include_body: bool = True
) -> list[dict]:
    """
    List emails from specified folder.
    
    Args:
        account_id: Account ID
        folder: Folder name (inbox, sent, drafts, deleted, junk)
        limit: Max number of emails
        include_body: Whether to include email body
    
    Returns:
        List of email objects
    """
    FOLDERS = {
        "inbox": "inbox",
        "sent": "sentitems",
        "drafts": "drafts",
        "deleted": "deleteditems",
        "junk": "junkemail",
    }
    
    folder_path = FOLDERS.get(folder.lower(), "inbox")
    
    select_fields = "id,subject,from,toRecipients,receivedDateTime,isRead,hasAttachments"
    if include_body:
        select_fields += ",body"
    
    params = {
        "$select": select_fields,
        "$top": min(limit, 100),
        "$orderby": "receivedDateTime desc"
    }
    
    result = await request(
        "GET",
        f"/me/mailFolders/{folder_path}/messages",
        account_id,
        params=params
    )
    
    return result.get("value", [])


async def get_email(
    email_id: str,
    account_id: Optional[str] = None
) -> dict:
    """Get specific email by ID"""
    return await request("GET", f"/me/messages/{email_id}", account_id)


async def search_emails(
    query: str,
    account_id: Optional[str] = None,
    limit: int = 10
) -> list[dict]:
    """
    Search for emails.
    
    Args:
        query: Search query
        account_id: Account ID
        limit: Max results
    
    Returns:
        List of matching emails
    """
    params = {
        "$search": f'"{query}"',
        "$top": min(limit, 100),
        "$orderby": "receivedDateTime desc"
    }
    
    result = await request("GET", "/me/messages", account_id, params=params)
    return result.get("value", [])
