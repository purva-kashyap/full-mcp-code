"""Mock Microsoft Graph API client for testing without credentials"""
import sys
from typing import Any, Optional, List, Dict
sys.path.append('..')
from mock_data import (
    get_mock_users,
    get_mock_user,
    get_mock_emails,
    get_mock_email,
    search_mock_emails,
    get_mock_teams,
    get_mock_team_members,
    get_mock_channels,
    get_mock_channel_messages,
    get_mock_calendar_events,
    get_mock_online_meetings
)


async def request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> Any:
    """
    Mock Graph API request - returns fake data without calling Microsoft.
    """
    print(f"[MOCK GRAPH] {method} {endpoint}", file=sys.stderr)
    
    # This is a mock - we just log the request
    return {"mock": True, "endpoint": endpoint}


async def get_user_profile(user_email: str) -> dict:
    """Get mock user profile"""
    print(f"[MOCK GRAPH] Getting user profile for {user_email}", file=sys.stderr)
    return get_mock_user(user_email)


async def list_users(limit: int = 10) -> List[Dict[str, Any]]:
    """List mock users"""
    print(f"[MOCK GRAPH] Listing {limit} users", file=sys.stderr)
    return get_mock_users(limit)


async def list_emails(
    user_email: str,
    limit: int = 10,
    folder: str = "inbox",
    filter_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List mock emails"""
    print(f"[MOCK GRAPH] Listing {limit} emails for {user_email} from {folder}", file=sys.stderr)
    return get_mock_emails(user_email, limit, folder)


async def get_email(user_email: str, email_id: str) -> Dict[str, Any]:
    """Get mock email details"""
    print(f"[MOCK GRAPH] Getting email {email_id} for {user_email}", file=sys.stderr)
    return get_mock_email(user_email, email_id)


async def search_emails(
    user_email: str,
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search mock emails"""
    print(f"[MOCK GRAPH] Searching emails for {user_email} with query: {query}", file=sys.stderr)
    return search_mock_emails(user_email, query, limit)


async def list_teams() -> List[Dict[str, Any]]:
    """List mock teams"""
    print("[MOCK GRAPH] Listing teams", file=sys.stderr)
    return get_mock_teams()


async def get_team_members(team_id: str) -> List[Dict[str, Any]]:
    """Get mock team members"""
    print(f"[MOCK GRAPH] Getting members for team {team_id}", file=sys.stderr)
    return get_mock_team_members(team_id)


async def list_team_channels(team_id: str) -> List[Dict[str, Any]]:
    """List mock team channels"""
    print(f"[MOCK GRAPH] Listing channels for team {team_id}", file=sys.stderr)
    return get_mock_channels(team_id)


async def get_channel_messages(
    team_id: str,
    channel_id: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Get mock channel messages"""
    print(f"[MOCK GRAPH] Getting messages for channel {channel_id} in team {team_id}", file=sys.stderr)
    return get_mock_channel_messages(team_id, channel_id, limit)


async def list_calendar_events(
    user_email: str,
    start_datetime: Optional[str] = None,
    end_datetime: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """List mock calendar events"""
    print(f"[MOCK GRAPH] Listing calendar events for {user_email}", file=sys.stderr)
    return get_mock_calendar_events(user_email, limit)


async def get_calendar_event(user_email: str, event_id: str) -> Dict[str, Any]:
    """Get mock calendar event"""
    print(f"[MOCK GRAPH] Getting calendar event {event_id} for {user_email}", file=sys.stderr)
    events = get_mock_calendar_events(user_email, 10)
    for event in events:
        if event["id"] == event_id:
            return event
    return events[0] if events else {}


async def list_user_online_meetings(
    user_email: str,
    start_datetime: Optional[str] = None,
    end_datetime: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """List mock online meetings"""
    print(f"[MOCK GRAPH] Listing online meetings for {user_email}", file=sys.stderr)
    return get_mock_online_meetings(user_email, limit)


async def get_online_meeting(user_email: str, meeting_id: str) -> Dict[str, Any]:
    """Get mock online meeting"""
    print(f"[MOCK GRAPH] Getting online meeting {meeting_id}", file=sys.stderr)
    meetings = get_mock_online_meetings(user_email, 5)
    for meeting in meetings:
        if meeting["id"] == meeting_id:
            return meeting
    return meetings[0] if meetings else {}


async def get_meeting_attendance_reports(user_email: str, meeting_id: str) -> List[Dict[str, Any]]:
    """Get mock attendance reports"""
    print(f"[MOCK GRAPH] Getting attendance reports for meeting {meeting_id}", file=sys.stderr)
    return [
        {
            "id": f"report-{meeting_id}",
            "meetingStartDateTime": "2024-01-15T10:00:00Z",
            "meetingEndDateTime": "2024-01-15T11:00:00Z",
            "totalParticipantCount": 5
        }
    ]


async def get_meeting_attendees(user_email: str, meeting_id: str, report_id: str) -> List[Dict[str, Any]]:
    """Get mock meeting attendees"""
    print(f"[MOCK GRAPH] Getting attendees for report {report_id}", file=sys.stderr)
    return [
        {
            "displayName": user["displayName"],
            "emailAddress": user["mail"],
            "role": "Presenter" if i == 0 else "Attendee",
            "totalAttendanceInSeconds": 3600 - (i * 300)
        }
        for i, user in enumerate(get_mock_users(5))
    ]


async def list_meeting_transcripts(user_email: str, meeting_id: str) -> List[Dict[str, Any]]:
    """List mock transcripts"""
    print(f"[MOCK GRAPH] Listing transcripts for meeting {meeting_id}", file=sys.stderr)
    return [
        {
            "id": f"transcript-{meeting_id}",
            "meetingId": meeting_id,
            "createdDateTime": "2024-01-15T11:05:00Z"
        }
    ]


async def get_transcript_content(user_email: str, meeting_id: str, transcript_id: str) -> str:
    """Get mock transcript content"""
    print(f"[MOCK GRAPH] Getting transcript content for {transcript_id}", file=sys.stderr)
    return """
[00:00] John Doe: Good morning everyone, let's get started.
[00:15] Jane Smith: Thanks for joining. I'll share my screen.
[01:30] Sarah Johnson: I have a question about the timeline.
[02:00] John Doe: Great question. Let me address that...
[05:00] Meeting ended.
"""


async def list_meeting_recordings(user_email: str, meeting_id: str) -> List[Dict[str, Any]]:
    """List mock recordings"""
    print(f"[MOCK GRAPH] Listing recordings for meeting {meeting_id}", file=sys.stderr)
    return [
        {
            "id": f"recording-{meeting_id}",
            "meetingId": meeting_id,
            "recordingContentUrl": f"https://mock-recording-url.com/{meeting_id}",
            "createdDateTime": "2024-01-15T11:05:00Z"
        }
    ]
