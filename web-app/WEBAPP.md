# Web Application for Microsoft 365 Email Reader

Beautiful web interface to authenticate users and read their Microsoft 365 emails.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│                 │      │                  │      │                 │
│  User Browser   │◄────►│  Flask Web App   │◄────►│   MCP Server    │
│  (Frontend)     │      │  (webapp.py)     │      │   (main.py)     │
│                 │      │                  │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                                            │
                                                            ▼
                                                    ┌─────────────────┐
                                                    │ Callback Server │
                                                    │ (Port 8000)     │
                                                    └─────────────────┘
```

## Features

✅ **Beautiful UI** - Modern, responsive design  
✅ **OAuth Flow** - Seamless Microsoft authentication  
✅ **Session Management** - Secure user sessions  
✅ **Email Reading** - View inbox, sent, drafts  
✅ **Real-time Polling** - Automatic callback detection  

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Callback Server (Terminal 1)

```bash
cd ../callback-server
python3 oauth_callback_server.py
```

### 3. Start the MCP Server (Terminal 2)

```bash
cd microsoft-mcp
python3 main.py
```

### 4. Start the Web App (Terminal 3)

```bash
cd microsoft-mcp
python3 webapp.py
```

### 5. Open Browser

Navigate to: **http://localhost:5000**

## How It Works

### Authentication Flow:

1. **User clicks "Sign in with Microsoft"**
   - Frontend calls `/api/start-auth`
   - Backend calls MCP server's `authenticate_account` tool
   - Returns auth URL to frontend

2. **Browser opens OAuth popup**
   - User signs in with Microsoft
   - Microsoft redirects to callback server (port 8000)
   - Callback server stores the auth code

3. **Frontend polls for completion**
   - Every 2 seconds, calls `/api/check-callback`
   - Backend calls MCP server's `wait_for_callback` tool
   - MCP server polls callback server API

4. **Authentication completes**
   - Backend calls `complete_authentication` tool
   - Stores user info in Flask session
   - Frontend redirects to dashboard

### Email Reading:

1. **User clicks "Inbox"**
   - Frontend calls `/api/emails?folder=inbox&limit=10`
   - Backend calls MCP server's `list_emails` tool
   - Returns formatted email list

2. **Display emails**
   - Show subject, sender, date, preview
   - Click to view full email (implement as needed)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page / Dashboard |
| `/api/start-auth` | POST | Start OAuth flow |
| `/api/check-callback` | POST | Poll for callback completion |
| `/api/emails` | GET | Get emails (inbox/sent/drafts) |
| `/api/email/<id>` | GET | Get specific email |
| `/logout` | GET | Clear session and logout |

## Configuration

### Environment Variables (.env)

```bash
# Same as MCP server
MICROSOFT_MCP_CLIENT_ID=your-client-id
MICROSOFT_MCP_CLIENT_SECRET=your-client-secret
MICROSOFT_MCP_ENABLE_CALLBACK_SERVER=false
MICROSOFT_MCP_REDIRECT_URI=http://localhost:8000/callback
MICROSOFT_MCP_OAUTH_CALLBACK_API_URL=http://localhost:8000/api/callback/{state}
```

### Flask Session Secret

The app generates a random secret key on startup. For production, set:

```python
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
```

## Multi-User Support

✅ **Session-based** - Each user has their own Flask session  
✅ **State tracking** - OAuth state stored per session  
✅ **Concurrent auth** - Multiple users can authenticate simultaneously  
✅ **Account isolation** - Each user's emails are separate  

## Security Considerations

🔒 **HTTPS in Production** - Always use HTTPS for production  
🔒 **Secure Cookies** - Set `SESSION_COOKIE_SECURE=True` for production  
🔒 **CSRF Protection** - Add Flask-WTF for CSRF tokens  
🔒 **State Validation** - OAuth state is verified on callback  

## Customization

### Change Styling

Edit `templates/index.html` and `templates/dashboard.html` CSS sections.

### Add Email Details View

Implement the `viewEmail()` function in `dashboard.html`:

```javascript
async function viewEmail(emailId) {
    const response = await fetch(`/api/email/${emailId}`);
    const data = await response.json();
    // Display email in modal or new page
}
```

### Add Search Functionality

Call the `search_emails` MCP tool:

```python
@app.route('/api/search', methods=['POST'])
def search_emails():
    query = request.json.get('query')
    emails = asyncio.run(call_mcp_server('search_emails', {
        'account_id': session['account_id'],
        'query': query,
        'limit': 20
    }))
    return jsonify({'success': True, 'emails': emails})
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 webapp:app
```

### Using Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_SECRET_KEY=your-production-secret
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "webapp:app"]
```

### Environment Variables for Production

```bash
FLASK_ENV=production
FLASK_SECRET_KEY=generate-secure-random-key
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

## Troubleshooting

### Authentication Window Not Closing

Check popup blocker settings in browser.

### Session Lost After Refresh

Ensure `app.secret_key` is consistent across app restarts.

### Emails Not Loading

Verify MCP server is running and accessible at `http://0.0.0.0:8001/mcp/`.

## Next Steps

- [ ] Add email composition
- [ ] Implement email search
- [ ] Add folder management
- [ ] Support attachments download
- [ ] Add calendar integration
- [ ] Implement dark mode

## License

MIT
