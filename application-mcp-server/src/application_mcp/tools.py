"""MCP tools for Microsoft Graph using Application permissions"""
import sys
from typing import Any
from . import graph
from .mcp_instance import mcp


# ============================================================================
# Utility Tools
# ============================================================================

@mcp.tool
def list_tools() -> list[dict[str, str]]:
    """
    List all available MCP tools with descriptions.
    
    Returns:
        List of tools with name and description
    """
    tools = [
        {
            "name": "list_tools",
            "description": "List all available MCP tools with descriptions"
        },
        {
            "name": "list_users",
            "description": "List users in the organization (for discovering available mailboxes)"
        },
        {
            "name": "get_user_profile",
            "description": "Get user profile information for any user in the organization"
        },
        {
            "name": "list_emails",
            "description": "List emails from any user's mailbox"
        },
        {
            "name": "get_email",
            "description": "Get full details of a specific email from any user's mailbox"
        },
        {
            "name": "search_emails",
            "description": "Search emails in any user's mailbox using query syntax"
        },
        {
            "name": "list_teams",
            "description": "List all Microsoft Teams in the organization"
        },
        {
            "name": "get_team_members",
            "description": "Get members of a specific team"
        },
        {
            "name": "list_team_channels",
            "description": "List channels in a specific team"
        },
        {
            "name": "get_channel_messages",
            "description": "Get messages from a specific team channel"
        }
    ]
    return tools


# ============================================================================
# User Management Tools
# ============================================================================

@mcp.tool
async def list_users(limit: int = 10) -> list[dict[str, Any]]:
    """
    List users in the organization.
    
    Useful for discovering which users' mailboxes you can access.
    Note: External guest users (with #EXT# in UPN) typically don't have mailboxes.
    
    Args:
        limit: Maximum number of users to return (default 10, max 100)
    
    Returns:
        List of users with id, displayName, mail, userPrincipalName, userType, and isExternal
    """
    users = await graph.list_users(limit=limit)
    
    # Return simplified user info with type indicator
    return [
        {
            "id": u.get("id", ""),
            "displayName": u.get("displayName", ""),
            "email": u.get("mail") or u.get("userPrincipalName", ""),
            "userPrincipalName": u.get("userPrincipalName", ""),
            "userType": u.get("userType", "Member"),
            "isExternal": "#EXT#" in u.get("userPrincipalName", "")
        }
        for u in users
    ]


@mcp.tool
async def get_user_profile(user_email: str) -> dict[str, Any]:
    """
    Get user profile information for any user in the organization.
    
    Args:
        user_email: User's email address or userPrincipalName (e.g., "user@contoso.com")
    
    Returns:
        User profile with displayName, mail, userPrincipalName, etc.
    """
    result = await graph.get_user_profile(user_email)
    
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
    user_email: str,
    folder: str = "inbox",
    limit: int = 10,
    include_body: bool = True,
) -> list[dict[str, Any]]:
    """
    List emails from a user's mailbox folder.
    
    With application permissions, you can access any user's mailbox
    without requiring them to sign in.
    
    Args:
        user_email: User's email address or userPrincipalName (e.g., "user@contoso.com")
        folder: Folder name (inbox, sent, drafts, deleted, junk)
        limit: Maximum number of emails to return (default 10, max 100)
        include_body: Whether to include email body content
    
    Returns:
        List of email objects with subject, from, to, date, body, etc.
    """
    print(f"[TOOL] list_emails called with user_email={user_email}, folder={folder}, limit={limit}", file=sys.stderr)
    
    try:
        emails = await graph.list_emails(
            user_email=user_email,
            folder=folder,
            limit=limit,
            include_body=include_body
        )
        print(f"[TOOL] Retrieved {len(emails)} emails", file=sys.stderr)
        return emails
    except Exception as e:
        print(f"[TOOL] ERROR in list_emails: {e}", file=sys.stderr)
        raise


@mcp.tool
async def get_email(user_email: str, email_id: str) -> dict[str, Any]:
    """
    Get specific email by ID from a user's mailbox.
    
    Args:
        user_email: User's email address or userPrincipalName
        email_id: The unique identifier of the email message
    
    Returns:
        Email object with full details
    """
    return await graph.get_email(user_email, email_id)


@mcp.tool
async def search_emails(
    user_email: str,
    query: str = "",
    limit: int = 10,
    filter: str = ""
) -> list[dict[str, Any]]:
    """
    Search for emails in a user's mailbox using query and/or filter.
    
    At least one of 'query' or 'filter' must be provided.
    
    Args:
        user_email: User's email address or userPrincipalName
        query: Optional search query string (e.g., "from:john@example.com subject:meeting")
        limit: Maximum results (default 10, max 100)
        filter: Optional OData filter (e.g., "isRead eq false", "hasAttachments eq true", 
                "from/emailAddress/address eq 'user@example.com'")
    
    Returns:
        List of matching emails
        
    Raises:
        ValueError: If neither query nor filter is provided
    """
    if not query and not filter:
        raise ValueError("At least one of 'query' or 'filter' must be provided")
    
    return await graph.search_emails(
        user_email, 
        query=query if query else None, 
        limit=limit, 
        filter_query=filter if filter else None
    )


# ============================================================================
# Microsoft Teams Tools
# ============================================================================

@mcp.tool
async def list_teams(limit: int = 25) -> list[dict[str, Any]]:
    """
    List all Microsoft Teams in the organization.
    
    Requires Group.Read.All or Group.ReadWrite.All application permission.
    
    Args:
        limit: Maximum number of teams to return (default 25, max 100)
    
    Returns:
        List of team objects with id, displayName, description, visibility, createdDateTime
    """
    teams = await graph.list_teams(limit=limit)
    return [
        {
            "id": t.get("id", ""),
            "displayName": t.get("displayName", ""),
            "description": t.get("description", ""),
            "visibility": t.get("visibility", ""),
            "createdDateTime": t.get("createdDateTime", "")
        }
        for t in teams
    ]


@mcp.tool
async def get_team_members(team_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """
    Get members of a specific Microsoft Team.
    
    Requires TeamMember.Read.All or TeamMember.ReadWrite.All application permission.
    
    Args:
        team_id: The ID of the team
        limit: Maximum number of members to return (default 100, max 100)
    
    Returns:
        List of team member objects with roles and user information
    """
    members = await graph.get_team_members(team_id, limit=limit)
    return [
        {
            "id": m.get("id", ""),
            "displayName": m.get("displayName", ""),
            "userId": m.get("userId", ""),
            "email": m.get("email", ""),
            "roles": m.get("roles", [])
        }
        for m in members
    ]


@mcp.tool
async def list_team_channels(team_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """
    List channels in a specific Microsoft Team.
    
    Requires Channel.ReadBasic.All, ChannelSettings.Read.All, or higher application permission.
    
    Args:
        team_id: The ID of the team
        limit: Maximum number of channels to return (default 50, max 100)
    
    Returns:
        List of channel objects with id, displayName, description, membershipType
    """
    channels = await graph.list_team_channels(team_id, limit=limit)
    return [
        {
            "id": c.get("id", ""),
            "displayName": c.get("displayName", ""),
            "description": c.get("description", ""),
            "membershipType": c.get("membershipType", ""),
            "createdDateTime": c.get("createdDateTime", "")
        }
        for c in channels
    ]


@mcp.tool
async def get_channel_messages(
    team_id: str,
    channel_id: str,
    limit: int = 50
) -> list[dict[str, Any]]:
    """
    Get messages from a specific team channel.
    
    Requires ChannelMessage.Read.All application permission.
    
    Args:
        team_id: The ID of the team
        channel_id: The ID of the channel
        limit: Maximum number of messages to return (default 50, max 50)
    
    Returns:
        List of message objects with content, sender, and timestamp information
    """
    messages = await graph.get_channel_messages(team_id, channel_id, limit=limit)
    return [
        {
            "id": m.get("id", ""),
            "createdDateTime": m.get("createdDateTime", ""),
            "from": m.get("from", {}),
            "body": m.get("body", {}),
            "attachments": m.get("attachments", []),
            "mentions": m.get("mentions", []),
            "replyToId": m.get("replyToId")
        }
        for m in messages
    ]
