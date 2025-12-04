"""Microsoft Graph API client using Application permissions"""
import sys
import httpx
from typing import Any, Optional
from . import auth


async def request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> Any:
    """
    Make a request to Microsoft Graph API using application permissions.
    
    With application permissions, endpoints use /users/{userPrincipalName} 
    instead of /me since there's no authenticated user context.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., "/users/user@contoso.com/messages")
        params: Query parameters
        json_data: JSON body data
    
    Returns:
        Response JSON data
    """
    token = auth.get_token()
    
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
            error_text = response.text
            print(f"[GRAPH] Error {response.status_code}: {error_text}", file=sys.stderr)
            
            # Provide helpful error messages
            if response.status_code == 404:
                if '/users/' in endpoint:
                    user_id = endpoint.split('/users/')[1].split('/')[0]
                    print(f"[GRAPH] User not found: {user_id}", file=sys.stderr)
                    print(f"[GRAPH] This could be an external user or the user doesn't exist", file=sys.stderr)
                if '/mailFolders/' in endpoint or '/messages' in endpoint:
                    print(f"[GRAPH] User may not have a mailbox (external guest users often don't)", file=sys.stderr)
            elif response.status_code == 403:
                print(f"[GRAPH] Permission denied - check application permissions", file=sys.stderr)
            
            response.raise_for_status()
        
        return response.json()


async def get_user_profile(user_email: str) -> dict:
    """
    Get user profile information using application permissions.
    
    Args:
        user_email: User's email address or userPrincipalName (e.g., "user@contoso.com")
    
    Returns:
        User profile object
    """
    return await request("GET", f"/users/{user_email}")


async def list_emails(
    user_email: str,
    folder: str = "inbox",
    limit: int = 10,
    include_body: bool = True
) -> list[dict]:
    """
    List emails from a specified user's mailbox folder.
    
    With application permissions, the app can access any user's mailbox
    without that user being signed in.
    
    Args:
        user_email: User's email address or userPrincipalName
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
        f"/users/{user_email}/mailFolders/{folder_path}/messages",
        params=params
    )
    
    return result.get("value", [])


async def get_email(user_email: str, email_id: str) -> dict:
    """
    Get specific email by ID from a user's mailbox.
    
    Args:
        user_email: User's email address or userPrincipalName
        email_id: Email message ID
    
    Returns:
        Email object
    """
    return await request("GET", f"/users/{user_email}/messages/{email_id}")


async def search_emails(
    user_email: str,
    query: Optional[str] = None,
    limit: int = 10,
    filter_query: Optional[str] = None
) -> list[dict]:
    """
    Search for emails in a user's mailbox.
    
    Args:
        user_email: User's email address or userPrincipalName
        query: Optional search query string
        limit: Max results
        filter_query: Optional OData filter (e.g., "isRead eq false" or "hasAttachments eq true")
    
    Returns:
        List of matching emails
        
    Raises:
        ValueError: If neither query nor filter_query is provided
    """
    if not query and not filter_query:
        raise ValueError("At least one of 'query' or 'filter_query' must be provided")
    
    params = {
        "$top": min(limit, 100),
        "$orderby": "receivedDateTime desc"
    }
    
    if query:
        params["$search"] = f'"{query}"'
    
    if filter_query:
        params["$filter"] = filter_query
    
    result = await request("GET", f"/users/{user_email}/messages", params=params)
    return result.get("value", [])


async def list_users(limit: int = 10) -> list[dict]:
    """
    List users in the organization (useful for discovering available mailboxes).
    
    Note: This includes both organization users and external guest users.
    External users have '#EXT#' in their userPrincipalName and may not have mailboxes.
    
    Args:
        limit: Max number of users to return
    
    Returns:
        List of user objects
    """
    params = {
        "$select": "id,displayName,mail,userPrincipalName,userType",
        "$top": min(limit, 100),
    }
    
    result = await request("GET", "/users", params=params)
    return result.get("value", [])


# ============================================================================
# Microsoft Teams Functions
# ============================================================================

async def list_teams(limit: int = 25) -> list[dict]:
    """
    List all Microsoft Teams in the organization.
    
    Requires Group.Read.All or Group.ReadWrite.All permission.
    
    Args:
        limit: Max number of teams to return
    
    Returns:
        List of team objects
    """
    params = {
        "$filter": "resourceProvisioningOptions/Any(x:x eq 'Team')",
        "$select": "id,displayName,description,visibility,createdDateTime",
        "$top": min(limit, 100),
    }
    
    result = await request("GET", "/groups", params=params)
    return result.get("value", [])


async def get_team_members(team_id: str, limit: int = 100) -> list[dict]:
    """
    Get members of a specific team.
    
    Requires TeamMember.Read.All or TeamMember.ReadWrite.All permission.
    
    Args:
        team_id: The ID of the team
        limit: Max number of members to return
    
    Returns:
        List of team member objects
    """
    params = {
        "$top": min(limit, 100),
    }
    
    result = await request("GET", f"/teams/{team_id}/members", params=params)
    return result.get("value", [])


async def list_team_channels(team_id: str, limit: int = 50) -> list[dict]:
    """
    List channels in a specific team.
    
    Requires Channel.ReadBasic.All, ChannelSettings.Read.All, or higher permission.
    
    Args:
        team_id: The ID of the team
        limit: Max number of channels to return
    
    Returns:
        List of channel objects
    """
    params = {
        "$select": "id,displayName,description,membershipType,createdDateTime",
        "$top": min(limit, 100),
    }
    
    result = await request("GET", f"/teams/{team_id}/channels", params=params)
    return result.get("value", [])


async def get_channel_messages(
    team_id: str,
    channel_id: str,
    limit: int = 50
) -> list[dict]:
    """
    Get messages from a specific channel.
    
    Requires ChannelMessage.Read.All permission.
    
    Args:
        team_id: The ID of the team
        channel_id: The ID of the channel
        limit: Max number of messages to return
    
    Returns:
        List of message objects
    """
    params = {
        "$top": min(limit, 50),  # Graph API limits this to 50
        "$orderby": "createdDateTime desc"
    }
    
    result = await request(
        "GET",
        f"/teams/{team_id}/channels/{channel_id}/messages",
        params=params
    )
    return result.get("value", [])


async def list_user_online_meetings(
    user_email: str,
    limit: int = 50,
    filter_query: Optional[str] = None
) -> list[dict]:
    """
    List online meetings for a specific user.
    
    Requires OnlineMeetings.Read.All or OnlineMeetings.ReadWrite.All permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        limit: Max number of meetings to return
        filter_query: Optional OData filter (e.g., "startDateTime ge 2025-01-01T00:00:00Z")
    
    Returns:
        List of online meeting objects
    """
    params = {
        "$top": min(limit, 100),
        "$orderby": "createdDateTime desc"
    }
    
    if filter_query:
        params["$filter"] = filter_query
    
    result = await request("GET", f"/users/{user_email}/onlineMeetings", params=params)
    return result.get("value", [])


async def get_online_meeting(
    user_email: str,
    meeting_id: str
) -> dict:
    """
    Get details of a specific online meeting.
    
    Requires OnlineMeetings.Read.All or OnlineMeetings.ReadWrite.All permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        Online meeting object with full details
    """
    return await request("GET", f"/users/{user_email}/onlineMeetings/{meeting_id}")


async def get_meeting_attendance_reports(
    user_email: str,
    meeting_id: str
) -> list[dict]:
    """
    Get attendance reports for a specific online meeting.
    
    Requires OnlineMeetingArtifact.Read.All permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        List of attendance report objects
    """
    result = await request(
        "GET",
        f"/users/{user_email}/onlineMeetings/{meeting_id}/attendanceReports"
    )
    return result.get("value", [])


async def get_meeting_attendees(
    user_email: str,
    meeting_id: str,
    report_id: str
) -> list[dict]:
    """
    Get attendees from a specific attendance report.
    
    Requires OnlineMeetingArtifact.Read.All permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
        report_id: The ID of the attendance report
    
    Returns:
        List of attendee records
    """
    result = await request(
        "GET",
        f"/users/{user_email}/onlineMeetings/{meeting_id}/attendanceReports/{report_id}/attendanceRecords"
    )
    return result.get("value", [])


async def list_meeting_transcripts(
    user_email: str,
    meeting_id: str
) -> list[dict]:
    """
    List transcripts for a specific online meeting.
    
    Requires OnlineMeetingTranscript.Read.All permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        List of transcript metadata objects
    """
    result = await request(
        "GET",
        f"/users/{user_email}/onlineMeetings/{meeting_id}/transcripts"
    )
    return result.get("value", [])


async def get_transcript_content(
    user_email: str,
    meeting_id: str,
    transcript_id: str
) -> str:
    """
    Get the content of a specific meeting transcript.
    
    Requires OnlineMeetingTranscript.Read.All permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
        transcript_id: The ID of the transcript
    
    Returns:
        Transcript content as VTT format string
    """
    token = auth.get_token()
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
    
    headers = {
        "Authorization": f"Bearer {token}",
    }
    
    print(f"[GRAPH] GET /users/{user_email}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content", file=sys.stderr)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=url,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code >= 400:
            print(f"[GRAPH] Error {response.status_code}: {response.text}", file=sys.stderr)
            response.raise_for_status()
        
        return response.text


async def list_meeting_recordings(
    user_email: str,
    meeting_id: str
) -> list[dict]:
    """
    List recordings for a specific online meeting.
    
    Requires OnlineMeetingRecording.Read.All permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        meeting_id: The ID of the meeting
    
    Returns:
        List of recording metadata objects
    """
    result = await request(
        "GET",
        f"/users/{user_email}/onlineMeetings/{meeting_id}/recordings"
    )
    return result.get("value", [])


async def list_calendar_events(
    user_email: str,
    limit: int = 50,
    filter_query: Optional[str] = None
) -> list[dict]:
    """
    List calendar events for a user.
    
    Requires Calendars.Read or Calendars.ReadWrite permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        limit: Max number of events to return
        filter_query: Optional OData filter (e.g., "start/dateTime ge '2025-01-01T00:00:00'")
    
    Returns:
        List of calendar event objects
    """
    params = {
        "$select": "id,subject,start,end,organizer,attendees,isOnlineMeeting,onlineMeeting,location",
        "$top": min(limit, 100),
        "$orderby": "start/dateTime desc"
    }
    
    if filter_query:
        params["$filter"] = filter_query
    
    result = await request("GET", f"/users/{user_email}/events", params=params)
    return result.get("value", [])


async def get_calendar_event(
    user_email: str,
    event_id: str
) -> dict:
    """
    Get details of a specific calendar event.
    
    Requires Calendars.Read or Calendars.ReadWrite permission.
    
    Args:
        user_email: User's email address or userPrincipalName
        event_id: The ID of the event
    
    Returns:
        Calendar event object with full details
    """
    return await request("GET", f"/users/{user_email}/events/{event_id}")
