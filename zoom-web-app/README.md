# Zoom Meeting Transcript & Summary Web App

A Flask web application for viewing Zoom meeting recordings, transcripts, and AI-generated summaries. This version uses **mock data** for demonstration purposes.

## Features

- 📋 View list of recorded Zoom meetings
- 📝 Read full meeting transcripts with speaker labels
- 🤖 AI-generated meeting summaries with key points and action items
- 💾 Copy summaries and transcripts to clipboard
- 📥 Download meeting content as text file
- 🎨 Beautiful, responsive UI with Tailwind CSS

## Demo Accounts

The application includes mock data for two demo users:

- **user1@example.com** - John Doe (3 meetings)
  - Product Strategy Meeting
  - Weekly Team Sync
  - Client Presentation

- **user2@example.com** - Jane Smith (1 meeting)
  - Engineering Review

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5002
```

3. Enter one of the demo email addresses to view meetings.

## Project Structure

```
zoom-web-app/
├── app.py                 # Main Flask application with mock data
├── requirements.txt       # Python dependencies
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Home page with email input
│   ├── meetings.html     # Meetings list page
│   └── summary.html      # Transcript and summary viewer
└── README.md             # This file
```

## API Endpoints

### POST /list/meetings
Retrieve meetings for a user by email.

**Request:**
```json
{
  "email": "user1@example.com"
}
```

**Response:**
```json
{
  "user": {
    "id": "zoom_user_123",
    "email": "user1@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "meetings": [...],
  "total_count": 3
}
```

### GET /meeting/<meeting_id>/summary
Get transcript and AI summary for a specific meeting.

**Response:**
```json
{
  "meeting_id": "12345678901",
  "topic": "Product Strategy Meeting",
  "transcript": "...",
  "summary": "...",
  "generated_at": "2024-01-19T10:30:00"
}
```

## Mock Data

The application includes:
- 2 mock users
- 4 mock meetings with realistic content
- Full transcripts with multiple speakers
- AI-generated summaries with:
  - Key decisions
  - Action items
  - Key metrics
  - Next steps

## Future Enhancements

To connect to real Zoom data:

1. **Zoom OAuth Integration**
   - Add Zoom OAuth flow for authentication
   - Store access tokens securely

2. **Zoom API Integration**
   - Replace `MOCK_USERS` with Zoom API `/users/me`
   - Replace `MOCK_MEETINGS` with `/users/{userId}/recordings`
   - Fetch actual transcripts from Zoom Cloud Recordings

3. **Real AI Summaries**
   - Replace `mock_generate_summary()` with actual LLM API:
     - OpenAI GPT-4
     - Anthropic Claude
     - Azure OpenAI
   - Add prompt engineering for better summaries

4. **Database**
   - Store meeting summaries in database
   - Cache transcripts to avoid repeated API calls
   - User preferences and settings

5. **Additional Features**
   - Search across transcripts
   - Filter meetings by date range
   - Export to PDF
   - Share summaries via email
   - Meeting analytics dashboard

## Technology Stack

- **Backend**: Flask 3.0.0
- **Frontend**: HTML5, JavaScript (Vanilla)
- **Styling**: Tailwind CSS (CDN)
- **Mock Data**: In-memory Python dictionaries

## Notes

- This is a **demonstration application** with mock data
- No actual Zoom API calls are made
- No database or persistent storage
- No authentication required (uses email-based mock lookup)
- Designed to showcase UI/UX for meeting transcript viewing

## License

MIT License - Feel free to use and modify for your projects.
