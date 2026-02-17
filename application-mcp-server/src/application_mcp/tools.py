"""MCP tools for Microsoft Graph using Application permissions"""
import logging
from typing import Any
from . import graph
from .mcp_instance import mcp
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


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
        },
        {
            "name": "list_user_online_meetings",
            "description": "List online meetings for a user with optional filtering"
        },
        {
            "name": "get_online_meeting",
            "description": "Get details of a specific online meeting"
        },
        {
            "name": "get_meeting_attendance_reports",
            "description": "Get attendance reports for a meeting"
        },
        {
            "name": "get_meeting_attendees",
            "description": "Get attendee details from an attendance report"
        },
        {
            "name": "list_meeting_transcripts",
            "description": "List transcripts for a meeting"
        },
        {
            "name": "get_transcript_content",
            "description": "Get the content of a meeting transcript"
        },
        {
            "name": "list_meeting_recordings",
            "description": "List recordings for a meeting"
        },
        {
            "name": "list_calendar_events",
            "description": "List calendar events for a user with optional filtering"
        },
        {
            "name": "get_calendar_event",
            "description": "Get details of a specific calendar event"
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
    logger.debug(
        "Listing emails",
        extra={
            "user_email": user_email,
            "folder": folder,
            "limit": limit,
            "include_body": include_body
        }
    )
    
    emails = await graph.list_emails(
        user_email=user_email,
        folder=folder,
        limit=limit,
        include_body=include_body
    )
    
    logger.info(
        "Retrieved emails",
        extra={
            "user_email": user_email,
            "folder": folder,
            "count": len(emails)
        }
    )
    
    return emails


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
        ValidationError: If neither query nor filter is provided
    """
    if not query and not filter:
        raise ValidationError(
            "At least one of 'query' or 'filter' must be provided",
            details={"query": query, "filter": filter}
        )
    
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


# ============================================================================
# Microsoft Teams Meetings Tools
# ============================================================================

@mcp.tool
async def list_user_online_meetings(
    user_email: str,
    limit: int = 50,
    filter: str = ""
) -> list[dict[str, Any]]:
    """
    List online meetings for a specific user.
    
    Requires OnlineMeetings.Read.All application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        limit: Maximum number of meetings to return (default 50, max 100)
        filter: Optional OData filter (e.g., "startDateTime ge 2025-01-01T00:00:00Z",
                "endDateTime le 2025-12-31T23:59:59Z")
    
    Returns:
        List of online meeting objects with join URL, start/end times, participants
    """
    meetings = await graph.list_user_online_meetings(
        user_email,
        limit=limit,
        filter_query=filter if filter else None
    )
    return [
        {
            "id": m.get("id", ""),
            "subject": m.get("subject", ""),
            "startDateTime": m.get("startDateTime", ""),
            "endDateTime": m.get("endDateTime", ""),
            "joinUrl": m.get("joinUrl", ""),
            "participants": m.get("participants", {}),
            "createdDateTime": m.get("createdDateTime", "")
        }
        for m in meetings
    ]


@mcp.tool
async def get_online_meeting(
    user_email: str,
    meeting_id: str
) -> dict[str, Any]:
    """
    Get detailed information about a specific online meeting.
    
    Requires OnlineMeetings.Read.All application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        Complete meeting object with all details
    """
    return await graph.get_online_meeting(user_email, meeting_id)


@mcp.tool
async def get_meeting_attendance_reports(
    user_email: str,
    meeting_id: str
) -> list[dict[str, Any]]:
    """
    Get attendance reports for a specific meeting.
    
    Requires OnlineMeetingArtifact.Read.All application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        List of attendance report objects with report IDs and summary info
    """
    reports = await graph.get_meeting_attendance_reports(user_email, meeting_id)
    return [
        {
            "id": r.get("id", ""),
            "totalParticipantCount": r.get("totalParticipantCount", 0),
            "meetingStartDateTime": r.get("meetingStartDateTime", ""),
            "meetingEndDateTime": r.get("meetingEndDateTime", "")
        }
        for r in reports
    ]


@mcp.tool
async def get_meeting_attendees(
    user_email: str,
    meeting_id: str,
    report_id: str
) -> list[dict[str, Any]]:
    """
    Get detailed attendee information from a meeting attendance report.
    
    Requires OnlineMeetingArtifact.Read.All application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
        report_id: The ID of the attendance report
    
    Returns:
        List of attendee records with join/leave times and duration
    """
    attendees = await graph.get_meeting_attendees(user_email, meeting_id, report_id)
    return [
        {
            "id": a.get("id", ""),
            "emailAddress": a.get("emailAddress", ""),
            "displayName": a.get("identity", {}).get("displayName", ""),
            "role": a.get("role", ""),
            "totalAttendanceInSeconds": a.get("totalAttendanceInSeconds", 0),
            "joinDateTime": a.get("attendanceIntervals", [{}])[0].get("joinDateTime", "") if a.get("attendanceIntervals") else "",
            "leaveDateTime": a.get("attendanceIntervals", [{}])[0].get("leaveDateTime", "") if a.get("attendanceIntervals") else ""
        }
        for a in attendees
    ]


@mcp.tool
async def list_meeting_transcripts(
    user_email: str,
    meeting_id: str
) -> list[dict[str, Any]]:
    """
    List transcripts available for a specific meeting.
    
    Requires OnlineMeetingTranscript.Read.All application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        List of transcript metadata objects
    """
    transcripts = await graph.list_meeting_transcripts(user_email, meeting_id)
    return [
        {
            "id": t.get("id", ""),
            "createdDateTime": t.get("createdDateTime", ""),
            "transcriptContentUrl": t.get("transcriptContentUrl", "")
        }
        for t in transcripts
    ]


@mcp.tool
async def get_transcript_content(
    user_email: str,
    meeting_id: str,
    transcript_id: str
) -> str:
    """
    Get the actual content of a meeting transcript.
    
    Requires OnlineMeetingTranscript.Read.All application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
        transcript_id: The ID of the transcript
    
    Returns:
        Transcript content in VTT format (WebVTT with timestamps and speaker info)
    """
    return await graph.get_transcript_content(user_email, meeting_id, transcript_id)


@mcp.tool
async def list_meeting_recordings(
    user_email: str,
    meeting_id: str
) -> list[dict[str, Any]]:
    """
    List recordings available for a specific meeting.
    
    Requires OnlineMeetingRecording.Read.All application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        List of recording metadata objects with download URLs
    """
    recordings = await graph.list_meeting_recordings(user_email, meeting_id)
    return [
        {
            "id": r.get("id", ""),
            "createdDateTime": r.get("createdDateTime", ""),
            "recordingContentUrl": r.get("recordingContentUrl", "")
        }
        for r in recordings
    ]


@mcp.tool
async def list_calendar_events(
    user_email: str,
    limit: int = 50,
    filter: str = ""
) -> list[dict[str, Any]]:
    """
    List calendar events for a user (includes Teams meetings scheduled via calendar).
    
    Requires Calendars.Read or Calendars.ReadWrite application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        limit: Maximum number of events to return (default 50, max 100)
        filter: Optional OData filter (e.g., "start/dateTime ge '2025-01-01T00:00:00'",
                "isOnlineMeeting eq true")
    
    Returns:
        List of calendar event objects with meeting details
    """
    events = await graph.list_calendar_events(
        user_email,
        limit=limit,
        filter_query=filter if filter else None
    )
    return [
        {
            "id": e.get("id", ""),
            "subject": e.get("subject", ""),
            "start": e.get("start", {}),
            "end": e.get("end", {}),
            "organizer": e.get("organizer", {}),
            "attendees": e.get("attendees", []),
            "isOnlineMeeting": e.get("isOnlineMeeting", False),
            "onlineMeeting": e.get("onlineMeeting", {}),
            "location": e.get("location", {})
        }
        for e in events
    ]


@mcp.tool
async def get_calendar_event(
    user_email: str,
    event_id: str
) -> dict[str, Any]:
    """
    Get detailed information about a specific calendar event.
    
    Requires Calendars.Read or Calendars.ReadWrite application permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        event_id: The ID of the calendar event
    
    Returns:
        Complete calendar event object with all meeting details
    """
    return await graph.get_calendar_event(user_email, event_id)
