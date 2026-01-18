# Mock MCP Server - Testing Without Microsoft Credentials

This mock version of the Application MCP Server allows you to test and develop without requiring actual Microsoft 365 credentials.

## What's Included

### Mock Data Files

1. **`mock_data.py`** - Realistic fake data including:
   - 5 sample users (4 internal employees + 1 external guest)
   - Mock emails with various subjects and senders
   - 3 teams: Engineering, Product, Marketing
   - Team channels and messages
   - Calendar events and online meetings
   - Attendance reports and transcripts

2. **`src/application_mcp/mock_graph.py`** - Mock implementation of Microsoft Graph API calls

3. **`main_mock.py`** - Modified server entry point that uses mock data

4. **`test_mock.py`** - Test script to verify the mock server

## Quick Start

### 1. Start the Mock Server

```bash
cd application-mcp-server
python main_mock.py
```

You should see:
```
🚀 Starting MOCK Microsoft 365 Application MCP Server...
   - FastAPI: http://localhost:8000
   - MCP endpoint: http://localhost:8001/mcp
   - Health check: http://localhost:8000/health

⚠️  MOCK MODE ENABLED
   - No Azure credentials required
   - Returns realistic fake data
   - Perfect for testing and development
```

### 2. Test the Mock Server

In another terminal:

```bash
cd application-mcp-server
python test_mock.py
```

This will run through all the main features and show you the mock data.

### 3. Use with the AI Agent

Now you can test the AI agent with the mock server:

```bash
cd ../ai-agent

# Set up your environment (only need LLM API key, no Azure credentials)
cp .env.example .env
# Edit .env and add OPENAI_API_KEY or ANTHROPIC_API_KEY

# Run the agent
python agent.py
```

## Mock Data Details

### Sample Users

1. **John Doe** - Software Engineer (Engineering)
2. **Jane Smith** - Product Manager (Product)
3. **Sarah Johnson** - Senior Engineer (Engineering)
4. **Mike Wilson** - Marketing Manager (Marketing)
5. **Emily Brown** - External Guest/Consultant

### Sample Teams

1. **Engineering Team** - 12 members, 3 channels (General, Backend, Frontend)
2. **Product Team** - 5 members, 2 channels (General, Roadmap)
3. **Marketing Team** - 8 members, 2 channels (General, Campaigns)

### Sample Email Subjects

- "Weekly Team Sync"
- "Project Update: Q1 Goals"
- "Meeting Notes - Sprint Planning"
- "Code Review Request"
- "Question about API Design"
- "Urgent: Production Issue"
- And more...

## Testing Queries

Try these queries with the AI agent:

```
You: List all users in the organization
You: Show me recent emails from john.doe@company.com
You: What teams exist?
You: Who are the members of the Engineering team?
You: Search for emails about 'meeting'
You: Show me calendar events for jane.smith@company.com
```

## Customizing Mock Data

Edit `mock_data.py` to:
- Add more users
- Create different email subjects
- Add more teams
- Customize team memberships
- Modify calendar events

## Switching Between Mock and Real Server

### Use Mock Server (No credentials needed)
```bash
python main_mock.py
```

### Use Real Server (Requires Azure credentials)
```bash
python main.py
```

## Benefits of Mock Mode

✅ **No Setup Required** - No Azure app registration, no credentials
✅ **Fast Development** - Instant responses, no API rate limits
✅ **Consistent Data** - Same data every time for predictable testing
✅ **Offline Testing** - Works without internet connection
✅ **Free** - No API costs or quotas
✅ **Privacy** - No real data accessed

## Architecture

```
AI Agent → MCP Client → Mock MCP Server → Mock Graph API → Mock Data
                                           (fake_graph.py)   (mock_data.py)
```

The mock server intercepts all Graph API calls and returns fake data instead of calling Microsoft.

## Limitations

⚠️ Mock data is static and doesn't persist changes
⚠️ Limited to predefined data sets
⚠️ Some advanced queries may not work exactly like real API
⚠️ No real authentication flow

## Next Steps

Once you've tested with mock data and everything works:

1. Set up real Azure credentials (see main README.md)
2. Switch to `python main.py`
3. Test with real Microsoft 365 data
4. Deploy to production

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Or use different ports in main_mock.py
```

### Module Import Errors
```bash
# Make sure you're in the correct directory
cd application-mcp-server
python main_mock.py
```

### AI Agent Can't Connect
- Ensure mock server is running on port 8001
- Check MCP_SERVER_URL in ai-agent/.env is set to http://localhost:8001/mcp
