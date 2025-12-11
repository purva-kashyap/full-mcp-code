# Simple Zoom Transcript Viewer - For Backend Developers

A **super simple** Flask web app with mock data. No complex JavaScript, no fancy features - just plain HTML forms and server-side rendering.

## How It Works (Simple!)

1. **Home Page** (`/`) - HTML form with email input
2. **Meetings Page** (`/meetings?email=...`) - Server renders list of meetings
3. **Summary Page** (`/summary/<meeting_id>`) - Server renders transcript + AI summary

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Simple HTML + CSS (Tailwind CDN)
- **Data Flow**: Server-side rendering with Jinja2 templates
- **No JavaScript complexity**: Just basic form submissions and links

## File Structure

```
zoom-web-app/
├── app.py                 # Flask routes + mock data
├── templates/
│   ├── base.html         # Base template
│   ├── index.html        # Home page (form)
│   ├── meetings.html     # Meetings list (server-rendered)
│   ├── summary.html      # Transcript & summary (server-rendered)
│   └── error.html        # Error page
└── requirements.txt      # Flask dependency
```

## Quick Start

```bash
# Install Flask
pip3 install -r requirements.txt

# Run the app
python3 app.py

# Open browser
open http://localhost:5002
```

## Demo Accounts

- `user1@example.com` - 3 meetings
- `user2@example.com` - 1 meeting

## How Each Page Works

### 1. Home Page (`/`)
```html
<form action="/meetings" method="GET">
    <input type="email" name="email" required />
    <button type="submit">View Meetings</button>
</form>
```
Simple HTML form → submits to `/meetings?email=...`

### 2. Meetings Page (`/meetings`)
```python
@app.route('/meetings')
def meetings_page():
    email = request.args.get('email')  # Get email from URL
    user = MOCK_USERS.get(email)       # Lookup user
    meetings = MOCK_MEETINGS.get(user['id'])  # Get meetings
    return render_template('meetings.html', user=user, meetings=meetings)
```
Server looks up data → renders HTML with Jinja2

### 3. Summary Page (`/summary/<meeting_id>`)
```python
@app.route('/summary/<meeting_id>')
def summary_page(meeting_id):
    transcript = MOCK_TRANSCRIPTS.get(meeting_id)
    summary = mock_generate_summary(transcript)
    return render_template('summary.html', transcript=transcript, summary=summary)
```
Server generates summary → renders HTML

## No Complex Features

✅ Simple HTML forms  
✅ Server-side rendering  
✅ URL query parameters  
✅ Plain links (`<a href="...">`)  

❌ No JavaScript frameworks  
❌ No fetch() API calls  
❌ No sessionStorage  
❌ No client-side state management  

## Adding Real Zoom Data (Later)

To connect to real Zoom API:

1. **Replace `MOCK_USERS`** with Zoom OAuth login
2. **Replace `MOCK_MEETINGS`** with Zoom API call to `/users/{userId}/recordings`
3. **Replace `MOCK_TRANSCRIPTS`** with actual transcript download from Zoom
4. **Replace `mock_generate_summary()`** with real LLM API (OpenAI/Claude)

## Why This Approach?

- **Easier to understand** for backend developers
- **Easier to debug** - just view source in browser
- **Easier to modify** - no build steps, no bundlers
- **Follows Flask conventions** - standard request/response cycle

Perfect for prototyping and learning!
