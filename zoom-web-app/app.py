"""
Zoom Meeting Transcript & Summary Web App
Flask application with mock data for testing UI
"""
from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Mock Data - Replace with actual Zoom API calls later
MOCK_USERS = {
    "user1@example.com": {
        "id": "zoom_user_123",
        "email": "user1@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "user2@example.com": {
        "id": "zoom_user_456",
        "email": "user2@example.com",
        "first_name": "Jane",
        "last_name": "Smith"
    }
}

MOCK_MEETINGS = {
    "zoom_user_123": [
        {
            "uuid": "meeting_001",
            "id": "12345678901",
            "topic": "Product Strategy Meeting",
            "start_time": "2024-01-15T14:00:00Z",
            "duration": 60,
            "total_size": 125000000,
            "recording_count": 2,
            "share_url": "https://zoom.us/rec/share/mock123"
        },
        {
            "uuid": "meeting_002",
            "id": "12345678902",
            "topic": "Weekly Team Sync",
            "start_time": "2024-01-16T10:00:00Z",
            "duration": 45,
            "total_size": 95000000,
            "recording_count": 1,
            "share_url": "https://zoom.us/rec/share/mock456"
        },
        {
            "uuid": "meeting_003",
            "id": "12345678903",
            "topic": "Client Presentation",
            "start_time": "2024-01-17T15:30:00Z",
            "duration": 90,
            "total_size": 180000000,
            "recording_count": 3,
            "share_url": "https://zoom.us/rec/share/mock789"
        }
    ],
    "zoom_user_456": [
        {
            "uuid": "meeting_004",
            "id": "12345678904",
            "topic": "Engineering Review",
            "start_time": "2024-01-18T09:00:00Z",
            "duration": 120,
            "total_size": 250000000,
            "recording_count": 2,
            "share_url": "https://zoom.us/rec/share/mock101"
        }
    ]
}

MOCK_TRANSCRIPTS = {
    "12345678901": {
        "transcript": """Speaker 1: Good afternoon everyone. Let's begin our product strategy meeting.

Speaker 2: Thanks for organizing this. I'd like to discuss our Q1 roadmap first.

Speaker 1: Absolutely. We have three major initiatives planned. First is the mobile app redesign, second is the API modernization, and third is implementing the new analytics dashboard.

Speaker 3: The mobile redesign sounds exciting. What's the timeline?

Speaker 1: We're targeting end of February for beta release. The design team has already completed the mockups and user testing showed a 40% improvement in user satisfaction.

Speaker 2: That's impressive. For the API modernization, we need to ensure backward compatibility. Are we planning a phased rollout?

Speaker 1: Yes, exactly. We'll maintain the v1 API for at least 12 months while v2 is rolled out gradually. This gives our enterprise clients time to migrate.

Speaker 3: What about the analytics dashboard? How will that integrate with our existing tools?

Speaker 1: Great question. It will be a standalone module that connects via webhooks to our current systems. We're also adding real-time data processing capabilities.

Speaker 2: Sounds like a solid plan. Let's schedule follow-ups for each initiative. What are the key metrics we're tracking?

Speaker 1: For mobile, it's user engagement and retention rates. For API, it's adoption rate and performance benchmarks. For analytics, it's data accuracy and query response times.

Speaker 3: Perfect. I'll send out the detailed project plans by end of day. Any other questions?

Speaker 2: No, this looks comprehensive. Let's reconvene next week to review progress.

Speaker 1: Agreed. Thanks everyone for your time today."""
    },
    "12345678902": {
        "transcript": """Speaker 1: Morning team! Let's do our quick weekly sync.

Speaker 2: I finished the authentication module last week. Currently working on the user profile page.

Speaker 3: Nice work! I'm handling the backend API endpoints. Should have the user management routes done by tomorrow.

Speaker 1: Excellent progress. Any blockers?

Speaker 2: Just one - need the updated API documentation for the new endpoints.

Speaker 3: I'll have that to you this afternoon. It's almost ready.

Speaker 1: Perfect. What about testing?

Speaker 2: QA team reviewed the auth module. Found two minor bugs which I've already fixed. Will submit for regression testing today.

Speaker 3: I'll start writing unit tests for the API once the documentation is complete.

Speaker 1: Great teamwork everyone. Let's keep this momentum going. Meeting adjourned."""
    },
    "12345678903": {
        "transcript": """Speaker 1: Thank you all for joining today's client presentation.

Speaker 2: We're excited to show you the progress on your project.

Client: Looking forward to seeing what you've built.

Speaker 1: Let me start by sharing the dashboard. As you can see, we've implemented all the features from your requirements document.

Client: This looks fantastic! The interface is very intuitive.

Speaker 2: We focused heavily on user experience. We conducted three rounds of usability testing with your target demographic.

Client: I really like the data visualization. The charts are clear and actionable.

Speaker 1: Thank you. We used the latest charting library and optimized it for real-time data updates.

Client: What about mobile responsiveness?

Speaker 2: Great question. Let me switch to mobile view. Everything is fully responsive and we've optimized touch interactions.

Client: Impressive. What's the deployment timeline?

Speaker 1: We can deploy to staging next week for your team to test. Production deployment can happen two weeks after that, pending your approval.

Client: That works perfectly with our schedule. What about training materials?

Speaker 2: We're preparing comprehensive documentation and video tutorials. We'll also conduct two live training sessions for your team.

Client: Excellent. I'm very satisfied with what I'm seeing. Let's proceed with the plan.

Speaker 1: Wonderful! We'll send you the detailed deployment schedule and training agenda by tomorrow.

Client: Perfect. Thank you both for the great work."""
    },
    "12345678904": {
        "transcript": """Speaker 1: Let's start our engineering review. First item - system architecture.

Speaker 2: We've been analyzing the current microservices architecture. There are some bottlenecks in the payment service.

Speaker 3: Yes, I noticed that too. Response times spike during peak hours.

Speaker 1: What's causing the bottleneck?

Speaker 2: Database connection pooling is the main issue. We're exhausting the pool under high load.

Speaker 3: I recommend increasing the pool size and implementing connection recycling.

Speaker 1: Have we considered implementing a caching layer?

Speaker 2: Good point. Redis cache could help significantly. We could cache frequent queries and reduce database load.

Speaker 3: I'll create a proof of concept this week. We should also look at query optimization.

Speaker 1: Agreed. Let's prioritize this. What about the security audit findings?

Speaker 2: We addressed all critical vulnerabilities. Two medium-priority items remain - implementing rate limiting and enhancing audit logging.

Speaker 3: I can handle the rate limiting. Should have it done in three days.

Speaker 1: Perfect. For the audit logging, let's use a structured logging format and integrate with our monitoring system.

Speaker 2: I'll take that on. Any other technical debt we should tackle?

Speaker 3: The API documentation needs updating. Some endpoints have changed but docs weren't updated.

Speaker 1: Good catch. Let's make that a requirement - no PR merges without updated docs. Meeting adjourned."""
    }
}

def mock_generate_summary(transcript: str, meeting_topic: str) -> str:
    """Mock LLM summary generation - Replace with actual LLM API call later"""
    # Simple mock - in production, call OpenAI/Anthropic/etc
    
    summaries = {
        "Product Strategy Meeting": """📊 Meeting Summary:

🎯 Key Decisions:
• Q1 roadmap finalized with three major initiatives
• Mobile app redesign targeting end of February beta release
• API v2 rollout to maintain backward compatibility for 12 months
• Analytics dashboard to be standalone module with real-time capabilities

✅ Action Items:
• Design team: Complete mobile app mockups
• Engineering: Implement phased API rollout
• Product: Send detailed project plans by EOD
• Team: Schedule follow-ups for each initiative

📈 Key Metrics:
• Mobile: User engagement and retention rates
• API: Adoption rate and performance benchmarks
• Analytics: Data accuracy and query response times

🗓️ Next Steps:
• Reconvene next week for progress review
• Mobile beta release: End of February
• Maintain API v1 support: Minimum 12 months""",
        
        "Weekly Team Sync": """📊 Meeting Summary:

✅ Completed Work:
• Authentication module finished and tested
• Two minor bugs fixed in auth module

🚧 In Progress:
• User profile page (Frontend)
• User management API endpoints (Backend)
• API documentation update

🎯 Action Items:
• Backend: Complete user management routes by tomorrow
• Backend: Deliver updated API documentation this afternoon
• Frontend: Submit auth module for regression testing today
• Backend: Write unit tests for API after documentation is complete

🚀 Status: On track with no major blockers""",
        
        "Client Presentation": """📊 Meeting Summary:

🎉 Client Feedback: Very satisfied with progress

✅ Completed Features:
• All requirements from specification document implemented
• Intuitive user interface with focus on UX
• Three rounds of usability testing completed
• Data visualization with clear, actionable charts
• Fully responsive mobile design
• Real-time data updates optimized

📅 Timeline:
• Next week: Deploy to staging environment
• Two weeks later: Production deployment (pending approval)

📚 Deliverables:
• Comprehensive documentation
• Video tutorials
• Two live training sessions
• Deployment schedule (tomorrow)
• Training agenda (tomorrow)

🎯 Outcome: Project approved to proceed as planned""",
        
        "Engineering Review": """📊 Meeting Summary:

🔴 Critical Issues Identified:
• Payment service bottleneck during peak hours
• Database connection pool exhaustion
• API documentation outdated

✅ Solutions Proposed:
• Increase database connection pool size
• Implement connection recycling
• Add Redis caching layer for frequent queries
• Optimize database queries
• Implement rate limiting (3 days)
• Enhance audit logging with structured format

🔒 Security Updates:
• All critical vulnerabilities addressed
• Two medium-priority items remaining

🎯 Action Items:
• Backend: Create Redis cache proof of concept (this week)
• DevOps: Implement rate limiting (3 days)
• Backend: Enhance audit logging and integrate monitoring
• All: Update API documentation before PR merges (new requirement)

📝 Policy Change: No PR merges without updated documentation"""
    }
    
    # Return matching summary or generate generic one
    for topic, summary in summaries.items():
        if topic.lower() in meeting_topic.lower():
            return summary
    
    # Fallback generic summary
    return f"""📊 Meeting Summary for: {meeting_topic}

🎯 Key Discussion Points:
• Multiple topics covered in detail
• Team collaboration and updates shared
• Action items identified

✅ Outcomes:
• Progress reviewed
• Next steps defined
• Follow-ups scheduled

🗓️ Next Steps:
• Review meeting recording for details
• Complete assigned action items
• Schedule follow-up if needed"""


@app.route('/')
def index():
    """Home page with email input"""
    return render_template('index.html')


@app.route('/meetings')
def meetings_page():
    """Meetings list page - takes email and date range as query parameters"""
    email = request.args.get('email', '').strip().lower()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    if not email:
        # No email provided, redirect to home
        return render_template('error.html', 
                             error_message="Email is required. Please start from the home page.",
                             back_link="/")
    
    # Mock: Get user from email
    user = MOCK_USERS.get(email)
    
    if not user:
        return render_template('error.html',
                             error_message=f"User not found for email: {email}",
                             back_link="/")
    
    user_id = user['id']
    
    # Mock: Get meetings for user
    meetings = MOCK_MEETINGS.get(user_id, [])
    
    # Filter meetings by date range if provided
    if start_date or end_date:
        filtered_meetings = []
        for meeting in meetings:
            meeting_date = meeting['start_time'][:10]  # Get YYYY-MM-DD part
            
            # Check if meeting falls within date range
            if start_date and meeting_date < start_date:
                continue
            if end_date and meeting_date > end_date:
                continue
            
            filtered_meetings.append(meeting)
        
        meetings = filtered_meetings
    
    return render_template('meetings.html', 
                         user=user, 
                         meetings=meetings,
                         total_count=len(meetings),
                         email=email,
                         start_date=start_date,
                         end_date=end_date)


@app.route('/summary/<meeting_id>')
def summary_page(meeting_id):
    """Summary page with transcript and AI summary"""
    # Get parameters from query string
    email = request.args.get('email', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Get transcript data
    transcript_data = MOCK_TRANSCRIPTS.get(meeting_id)
    
    if not transcript_data:
        return render_template('error.html',
                             error_message=f"Transcript not found for meeting ID: {meeting_id}",
                             back_link="/")
    
    transcript = transcript_data['transcript']
    
    # Find meeting info to get topic
    meeting_topic = "Unknown Meeting"
    for user_id, meetings in MOCK_MEETINGS.items():
        for meeting in meetings:
            if meeting['id'] == meeting_id:
                meeting_topic = meeting['topic']
                break
    
    # Generate AI summary
    summary = mock_generate_summary(transcript, meeting_topic)
    
    return render_template('summary.html',
                         meeting_id=meeting_id,
                         topic=meeting_topic,
                         transcript=transcript,
                         summary=summary,
                         email=email,
                         start_date=start_date,
                         end_date=end_date)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    print(f"🚀 Starting development server on http://localhost:{port}")
    print("📝 Note: Using Flask development server (not for production)")
    app.run(host='0.0.0.0', port=port, debug=True)
