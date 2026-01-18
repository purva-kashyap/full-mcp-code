# Mock MCP Server + AI Agent Architecture

## Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                            │
│                    (Terminal / Command Line)                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ Natural Language Query
                                 │ "Show me emails from John"
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AI AGENT (agent.py)                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  LLM Provider (OpenAI GPT-4 / Anthropic Claude)             │   │
│  │  - Understands natural language                              │   │
│  │  - Decides which tools to call                               │   │
│  │  - Formats responses                                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MCP Client (FastMCP)                                        │   │
│  │  - Connects to MCP server                                    │   │
│  │  - Calls tools based on LLM decisions                        │   │
│  │  - Returns results to LLM                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ HTTP Request
                                 │ http://localhost:8001/mcp
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  MOCK MCP SERVER (main_mock.py)                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (Port 8000)                                  │   │
│  │  - Health checks                                             │   │
│  │  - Status endpoints                                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MCP Server (Port 8001)                                      │   │
│  │  - Exposes tools: list_users, list_emails, etc.             │   │
│  │  - Handles tool calls                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Tools Layer (tools.py)                                      │   │
│  │  @mcp.tool decorators                                        │   │
│  │  - list_users()                                              │   │
│  │  - list_emails()                                             │   │
│  │  - search_emails()                                           │   │
│  │  - list_teams()                                              │   │
│  │  - etc.                                                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ Call mock functions
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  MOCK GRAPH API (mock_graph.py)                      │
│  - get_mock_users()                                                 │
│  - get_mock_emails()                                                │
│  - search_mock_emails()                                             │
│  - get_mock_teams()                                                 │
│  - etc.                                                             │
│                                                                      │
│  ⚠️  NO MICROSOFT API CALLS - All data is fake!                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ Fetch from
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MOCK DATA (mock_data.py)                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MOCK_USERS                                                  │   │
│  │  - John Doe (Software Engineer)                             │   │
│  │  - Jane Smith (Product Manager)                             │   │
│  │  - Sarah Johnson (Senior Engineer)                          │   │
│  │  - Mike Wilson (Marketing Manager)                          │   │
│  │  - Emily Brown (External Guest)                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MOCK EMAILS                                                 │   │
│  │  - "Weekly Team Sync"                                       │   │
│  │  - "Project Update: Q1 Goals"                               │   │
│  │  - "Code Review Request"                                    │   │
│  │  - etc.                                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MOCK TEAMS                                                  │   │
│  │  - Engineering Team (12 members)                            │   │
│  │  - Product Team (5 members)                                 │   │
│  │  - Marketing Team (8 members)                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow Example

### Query: "Show me emails from john.doe@company.com"

```
1. USER
   └─> Types query in terminal

2. AI AGENT
   ├─> LLM analyzes: "Need to call list_emails tool"
   └─> MCP Client prepares request

3. MOCK MCP SERVER
   ├─> Receives: call_tool("list_emails", {"user_email": "john.doe@company.com"})
   └─> Routes to list_emails() function

4. TOOLS LAYER
   └─> Calls: graph.list_emails("john.doe@company.com")

5. MOCK GRAPH API
   └─> Calls: get_mock_emails("john.doe@company.com")

6. MOCK DATA
   ├─> Generates fake emails
   └─> Returns: [email1, email2, email3, ...]

[Response flows back up the chain]

7. AI AGENT
   ├─> Receives email data
   ├─> LLM formats response
   └─> Displays to user:
       "Here are the recent emails from John Doe's mailbox:
        1. Weekly Team Sync (from Jane Smith)
        2. Project Update (from Sarah Johnson)
        ..."
```

## File Structure

```
streamable-http-mcp/
│
├── application-mcp-server/           # MCP Server
│   ├── main.py                       # Real server (requires Azure)
│   ├── main_mock.py                  # Mock server (no credentials!)
│   ├── test_mock.py                  # Test script
│   ├── setup_mock.sh                 # Setup script
│   ├── mock_data.py                  # Fake data definitions
│   ├── requirements.txt
│   │
│   └── src/application_mcp/
│       ├── server.py                 # FastAPI server
│       ├── mcp_instance.py           # MCP instance
│       ├── tools.py                  # MCP tool definitions
│       ├── graph.py                  # Real MS Graph API
│       ├── mock_graph.py             # Mock MS Graph API
│       └── auth.py                   # Authentication (not used in mock)
│
└── ai-agent/                          # AI Agent
    ├── agent.py                       # Main agent code
    ├── example_queries.py             # Example queries
    ├── requirements.txt
    ├── .env.example                   # Config template
    ├── README.md
    └── USAGE.md
```

## Component Responsibilities

| Component | Responsibility | Mock vs Real |
|-----------|---------------|--------------|
| **AI Agent** | Natural language understanding, tool orchestration | Same for both |
| **MCP Client** | Communication with MCP server | Same for both |
| **MCP Server** | Expose tools, handle requests | Same for both |
| **Tools Layer** | Define available operations | Same for both |
| **Graph API** | Data access layer | **Different**: mock_graph.py vs graph.py |
| **Data Source** | Actual data | **Different**: mock_data.py vs Microsoft 365 |

## Environment Variables

### AI Agent (.env)
```env
# Required
LLM_PROVIDER=openai                    # or anthropic
OPENAI_API_KEY=sk-...                  # Your LLM API key

# Optional
MCP_SERVER_URL=http://localhost:8001/mcp
MAX_ITERATIONS=5
TEMPERATURE=0.7
```

### Mock MCP Server
```
NO ENVIRONMENT VARIABLES NEEDED! 🎉
```

### Real MCP Server (.env)
```env
# Required for real mode
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-secret
AZURE_TENANT_ID=your-tenant-id
```

## Ports Used

- **8000** - FastAPI health checks and status
- **8001** - MCP server endpoint (tool calls)
- **Network** - LLM API calls (OpenAI/Anthropic)

## Key Differences: Mock vs Real

### Mock Mode (main_mock.py)
✅ No Azure setup required
✅ No credentials needed
✅ Instant responses
✅ Consistent data
✅ Works offline
✅ Free to use
❌ Static data
❌ Can't modify data
❌ Limited to predefined scenarios

### Real Mode (main.py)
✅ Real Microsoft 365 data
✅ Live updates
✅ Full API capabilities
✅ Production-ready
❌ Requires Azure app registration
❌ Needs credentials
❌ Network dependent
❌ API quota limits

## Testing Strategy

```
1. Development Phase
   └─> Use MOCK mode
       - Fast iteration
       - No setup overhead
       - Test agent logic

2. Integration Testing
   └─> Use MOCK mode
       - Verify tool calls work
       - Test error handling
       - Validate responses

3. Pre-Production
   └─> Use REAL mode
       - Test with actual data
       - Verify permissions
       - Check performance

4. Production
   └─> Use REAL mode
       - Serve real users
       - Monitor usage
       - Handle real data
```

## Next Steps

1. ✅ Run mock server: `python main_mock.py`
2. ✅ Test it: `python test_mock.py`
3. ✅ Run AI agent: `cd ../ai-agent && python agent.py`
4. 🎯 Ask questions and see it work!
5. 🔧 Customize mock data if needed
6. 🚀 Switch to real mode when ready
