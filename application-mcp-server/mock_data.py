"""Mock data for testing without Microsoft credentials"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# Mock users
MOCK_USERS = [
    {
        "id": "user-001",
        "displayName": "John Doe",
        "mail": "john.doe@company.com",
        "userPrincipalName": "john.doe@company.com",
        "jobTitle": "Software Engineer",
        "department": "Engineering",
        "officeLocation": "Building 1, Floor 3",
        "userType": "Member",
        "mobilePhone": "+1-555-0101"
    },
    {
        "id": "user-002",
        "displayName": "Jane Smith",
        "mail": "jane.smith@company.com",
        "userPrincipalName": "jane.smith@company.com",
        "jobTitle": "Product Manager",
        "department": "Product",
        "officeLocation": "Building 1, Floor 2",
        "userType": "Member",
        "mobilePhone": "+1-555-0102"
    },
    {
        "id": "user-003",
        "displayName": "Sarah Johnson",
        "mail": "sarah.johnson@company.com",
        "userPrincipalName": "sarah.johnson@company.com",
        "jobTitle": "Senior Engineer",
        "department": "Engineering",
        "officeLocation": "Building 2, Floor 1",
        "userType": "Member",
        "mobilePhone": "+1-555-0103"
    },
    {
        "id": "user-004",
        "displayName": "Mike Wilson",
        "mail": "mike.wilson@company.com",
        "userPrincipalName": "mike.wilson@company.com",
        "jobTitle": "Marketing Manager",
        "department": "Marketing",
        "officeLocation": "Building 1, Floor 4",
        "userType": "Member",
        "mobilePhone": "+1-555-0104"
    },
    {
        "id": "user-005",
        "displayName": "Emily Brown (External)",
        "mail": "emily.brown@partner.com",
        "userPrincipalName": "emily.brown_partner.com#EXT#@company.onmicrosoft.com",
        "jobTitle": "Consultant",
        "department": None,
        "officeLocation": None,
        "userType": "Guest",
        "mobilePhone": None
    }
]

# Mock email subjects and bodies
EMAIL_SUBJECTS = [
    "Weekly Team Sync",
    "Project Update: Q1 Goals",
    "Meeting Notes - Sprint Planning",
    "Code Review Request",
    "Question about API Design",
    "Urgent: Production Issue",
    "Lunch Meeting Tomorrow?",
    "Quarterly Review Feedback",
    "New Feature Proposal",
    "Bug Report: Login Issue"
]

EMAIL_BODIES = [
    "Hi team,\n\nLet's sync up this Friday at 2pm to discuss our progress and next steps.\n\nBest,\n",
    "Hello,\n\nI wanted to share an update on the project. We're making good progress and should be on track for the deadline.\n\nThanks,\n",
    "Team,\n\nAttached are the notes from today's sprint planning meeting. Please review and let me know if you have questions.\n\nRegards,\n",
    "Hi,\n\nCould you please review this PR when you get a chance? I've addressed the feedback from the last review.\n\nThanks!\n",
    "Hey,\n\nI have a quick question about the API design for the new feature. Can we hop on a call?\n\nBest,\n",
    "URGENT: We have a production issue affecting users. Please join the war room ASAP.\n\nDetails in the incident ticket.\n",
    "Hi!\n\nWould you like to grab lunch tomorrow around noon? We can discuss the new project.\n\nLet me know!\n",
    "Hello,\n\nThank you for your hard work this quarter. Here's my feedback on your performance review.\n\nBest regards,\n",
    "Team,\n\nI have an idea for a new feature that could really help our users. Let's discuss in the next planning session.\n\nThanks,\n",
    "Hi,\n\nI'm experiencing issues logging into the application. Getting a 401 error. Can someone help?\n\nThanks,\n"
]

# Mock teams
MOCK_TEAMS = [
    {
        "id": "team-001",
        "displayName": "Engineering Team",
        "description": "Software Engineering and Development",
        "visibility": "private",
        "memberCount": 12
    },
    {
        "id": "team-002",
        "displayName": "Product Team",
        "description": "Product Management and Strategy",
        "visibility": "private",
        "memberCount": 5
    },
    {
        "id": "team-003",
        "displayName": "Marketing Team",
        "description": "Marketing and Communications",
        "visibility": "public",
        "memberCount": 8
    }
]

# Mock team channels
MOCK_CHANNELS = {
    "team-001": [
        {"id": "channel-001", "displayName": "General", "description": "General discussion"},
        {"id": "channel-002", "displayName": "Backend", "description": "Backend development"},
        {"id": "channel-003", "displayName": "Frontend", "description": "Frontend development"},
    ],
    "team-002": [
        {"id": "channel-004", "displayName": "General", "description": "General discussion"},
        {"id": "channel-005", "displayName": "Roadmap", "description": "Product roadmap planning"},
    ],
    "team-003": [
        {"id": "channel-006", "displayName": "General", "description": "General discussion"},
        {"id": "channel-007", "displayName": "Campaigns", "description": "Marketing campaigns"},
    ]
}

# Mock team memberships
MOCK_TEAM_MEMBERS = {
    "team-001": ["user-001", "user-003"],  # Engineering: John, Sarah
    "team-002": ["user-002"],  # Product: Jane
    "team-003": ["user-004"],  # Marketing: Mike
}


def get_mock_users(limit: int = 10) -> List[Dict[str, Any]]:
    """Get mock users"""
    return MOCK_USERS[:limit]


def get_mock_user(user_email: str) -> Dict[str, Any]:
    """Get a specific mock user"""
    for user in MOCK_USERS:
        if user["mail"] == user_email or user["userPrincipalName"] == user_email:
            return user
    # Return first user if not found
    return MOCK_USERS[0]


def get_mock_emails(user_email: str, limit: int = 10, folder: str = "inbox") -> List[Dict[str, Any]]:
    """Generate mock emails for a user"""
    user = get_mock_user(user_email)
    emails = []
    
    for i in range(min(limit, len(EMAIL_SUBJECTS))):
        # Pick a random sender (not the user themselves)
        sender = random.choice([u for u in MOCK_USERS if u["mail"] != user_email])
        
        # Generate timestamp (recent emails)
        timestamp = datetime.utcnow() - timedelta(days=i, hours=random.randint(0, 23))
        
        emails.append({
            "id": f"email-{user['id']}-{i:03d}",
            "subject": EMAIL_SUBJECTS[i],
            "bodyPreview": EMAIL_BODIES[i][:100] + "...",
            "body": {
                "contentType": "text",
                "content": EMAIL_BODIES[i] + sender["displayName"]
            },
            "from": {
                "emailAddress": {
                    "name": sender["displayName"],
                    "address": sender["mail"]
                }
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "name": user["displayName"],
                        "address": user["mail"]
                    }
                }
            ],
            "receivedDateTime": timestamp.isoformat() + "Z",
            "sentDateTime": timestamp.isoformat() + "Z",
            "hasAttachments": random.choice([True, False]),
            "importance": random.choice(["low", "normal", "high"]),
            "isRead": random.choice([True, False]),
            "conversationId": f"conv-{i:03d}"
        })
    
    return emails


def get_mock_email(user_email: str, email_id: str) -> Dict[str, Any]:
    """Get a specific mock email"""
    emails = get_mock_emails(user_email, limit=10)
    for email in emails:
        if email["id"] == email_id:
            return email
    # Return first email if not found
    return emails[0] if emails else None


def search_mock_emails(user_email: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search mock emails"""
    all_emails = get_mock_emails(user_email, limit=20)
    query_lower = query.lower()
    
    # Simple search in subject and body
    results = [
        email for email in all_emails
        if query_lower in email["subject"].lower() or query_lower in email["body"]["content"].lower()
    ]
    
    return results[:limit]


def get_mock_teams() -> List[Dict[str, Any]]:
    """Get mock teams"""
    return MOCK_TEAMS


def get_mock_team_members(team_id: str) -> List[Dict[str, Any]]:
    """Get members of a mock team"""
    user_ids = MOCK_TEAM_MEMBERS.get(team_id, [])
    members = []
    
    for user_id in user_ids:
        user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
        if user:
            members.append({
                "id": user_id,
                "displayName": user["displayName"],
                "email": user["mail"],
                "roles": ["member"]
            })
    
    return members


def get_mock_channels(team_id: str) -> List[Dict[str, Any]]:
    """Get channels for a mock team"""
    return MOCK_CHANNELS.get(team_id, [])


def get_mock_channel_messages(team_id: str, channel_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get mock channel messages"""
    messages = []
    
    for i in range(limit):
        sender = random.choice(MOCK_USERS)
        timestamp = datetime.utcnow() - timedelta(hours=i * 2)
        
        messages.append({
            "id": f"msg-{channel_id}-{i:03d}",
            "createdDateTime": timestamp.isoformat() + "Z",
            "body": {
                "content": f"This is message {i+1} in the channel. {random.choice(['Great work!', 'Thanks for the update.', 'Lets discuss this tomorrow.', 'Sounds good!'])}",
                "contentType": "text"
            },
            "from": {
                "user": {
                    "displayName": sender["displayName"],
                    "id": sender["id"]
                }
            }
        })
    
    return messages


def get_mock_calendar_events(user_email: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get mock calendar events"""
    user = get_mock_user(user_email)
    events = []
    
    event_subjects = [
        "Team Standup",
        "1:1 with Manager",
        "Project Planning",
        "Code Review Session",
        "Client Meeting",
        "Lunch Break",
        "Design Review",
        "All Hands Meeting"
    ]
    
    for i in range(min(limit, len(event_subjects))):
        start_time = datetime.utcnow() + timedelta(days=i, hours=random.randint(9, 17))
        end_time = start_time + timedelta(hours=1)
        
        events.append({
            "id": f"event-{user['id']}-{i:03d}",
            "subject": event_subjects[i],
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            },
            "organizer": {
                "emailAddress": {
                    "name": user["displayName"],
                    "address": user["mail"]
                }
            },
            "isOnlineMeeting": random.choice([True, False]),
            "location": {
                "displayName": random.choice(["Conference Room A", "Zoom", "Teams", "Office"])
            }
        })
    
    return events


def get_mock_online_meetings(user_email: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get mock online meetings"""
    user = get_mock_user(user_email)
    meetings = []
    
    for i in range(limit):
        start_time = datetime.utcnow() + timedelta(days=i)
        
        meetings.append({
            "id": f"meeting-{user['id']}-{i:03d}",
            "subject": f"Online Meeting {i+1}",
            "startDateTime": start_time.isoformat() + "Z",
            "endDateTime": (start_time + timedelta(hours=1)).isoformat() + "Z",
            "joinWebUrl": f"https://teams.microsoft.com/l/meetup-join/mock-meeting-{i}",
            "participants": {
                "organizer": {
                    "identity": {
                        "user": {
                            "displayName": user["displayName"]
                        }
                    }
                }
            }
        })
    
    return meetings
