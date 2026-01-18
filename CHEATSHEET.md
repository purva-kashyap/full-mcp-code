# 🚀 Quick Reference Cheat Sheet

## One-Command Start

```bash
./demo.sh
```

## Manual Start (3 Terminals)

### Terminal 1: Mock Server
```bash
cd application-mcp-server
python main_mock.py
```

### Terminal 2: AI Agent Setup
```bash
cd ai-agent
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY
python agent.py
```

### Terminal 3: Testing (Optional)
```bash
cd application-mcp-server
python test_mock.py
```

## Common Commands

### Start Mock Server
```bash
cd application-mcp-server && python main_mock.py
```

### Start Real Server (needs Azure credentials)
```bash
cd application-mcp-server && python main.py
```

### Test Mock Server
```bash
cd application-mcp-server && python test_mock.py
```

### Run AI Agent
```bash
cd ai-agent && python agent.py
```

### Run Example Queries
```bash
cd ai-agent && python example_queries.py
```

### Setup Everything
```bash
cd application-mcp-server && ./setup_mock.sh
```

## Example Queries

### Simple
```
List all users
Show me teams
Get profile for john.doe@company.com
```

### Email
```
Show me recent emails from john.doe@company.com
Search for emails about 'meeting'
Get the latest email from Jane
```

### Teams
```
Who are the members of Engineering team?
List all teams and their sizes
Show channels in the Product team
```

### Complex
```
Find all teams and show members of the first one
Get Engineering team members and their recent emails
Search for urgent emails in all mailboxes
```

## File Locations

| What | Where |
|------|-------|
| Mock Server | `application-mcp-server/main_mock.py` |
| Real Server | `application-mcp-server/main.py` |
| AI Agent | `ai-agent/agent.py` |
| Mock Data | `application-mcp-server/mock_data.py` |
| Agent Config | `ai-agent/.env` |

## Port Reference

- `8000` - FastAPI health checks
- `8001` - MCP server endpoint

## Configuration

### AI Agent (.env)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
MCP_SERVER_URL=http://localhost:8001/mcp
```

### Mock Server
No configuration needed! ✅

### Real Server (.env)
```env
AZURE_CLIENT_ID=your-id
AZURE_CLIENT_SECRET=your-secret
AZURE_TENANT_ID=your-tenant
```

## Troubleshooting

### Port in use
```bash
lsof -ti:8001 | xargs kill -9
```

### Can't connect
```bash
curl http://localhost:8001/mcp
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Documentation

- `QUICKSTART.md` - 5-minute start guide
- `ARCHITECTURE.md` - System diagrams
- `SUMMARY.md` - Project overview
- `README_COMPLETE.md` - Full documentation
- `ai-agent/README.md` - Agent overview
- `ai-agent/USAGE.md` - Agent usage
- `application-mcp-server/MOCK_SERVER.md` - Mock server

## URLs

- Health: http://localhost:8000/health
- MCP: http://localhost:8001/mcp
- Root: http://localhost:8000/

## Key Files Created

```
✨ ai-agent/
   - agent.py
   - example_queries.py
   - .env.example

✨ application-mcp-server/
   - main_mock.py
   - test_mock.py
   - mock_data.py
   - mock_graph.py

✨ Documentation
   - QUICKSTART.md
   - ARCHITECTURE.md
   - SUMMARY.md
   - README_COMPLETE.md
   - CHEATSHEET.md
```

## Quick Tests

### Test 1: Server Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Test 2: MCP Endpoint
```bash
curl http://localhost:8001/mcp
# Should connect (may need MCP client)
```

### Test 3: Full Test Suite
```bash
python test_mock.py
# Should show all tests passing
```

## Stop Everything

```bash
# Find and kill MCP server
lsof -ti:8001 | xargs kill -9

# Stop AI agent
Ctrl+C in agent terminal
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Port already in use | `lsof -ti:8001 \| xargs kill -9` |
| Can't connect | Check server is running |
| LLM errors | Verify API key in .env |
| Import errors | `pip install -r requirements.txt` |

## Environment Variables

### Required for AI Agent
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### Optional
- `LLM_PROVIDER` (default: openai)
- `OPENAI_MODEL` (default: gpt-4-turbo-preview)
- `MCP_SERVER_URL` (default: http://localhost:8001/mcp)
- `TEMPERATURE` (default: 0.7)
- `MAX_TOKENS` (default: 2000)
- `MAX_ITERATIONS` (default: 5)

## Mock Data

- 5 users (4 internal, 1 external)
- 10+ email subjects
- 3 teams (Engineering, Product, Marketing)
- Calendar events
- Online meetings
- Team channels

## Switching Modes

### Mock → Real
1. Set up Azure app
2. Add credentials to .env
3. Use `python main.py`

### Real → Mock
1. Use `python main_mock.py`
2. No .env needed!

## Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed
- [ ] LLM API key added to .env
- [ ] Mock server running (port 8001)
- [ ] Ready to chat!

---

**Pro Tip**: Keep this file open while working! 📌
