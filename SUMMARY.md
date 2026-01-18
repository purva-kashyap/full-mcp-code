# 🤖 AI Agent with Mock MCP Server - Complete Setup

Test your AI agent with **realistic fake data** - **NO Microsoft credentials required!**

## 🎯 What You Get

1. **Mock MCP Server** - Returns realistic fake Microsoft 365 data
2. **AI Agent** - Uses LLM (GPT-4/Claude) to answer questions naturally
3. **Complete Integration** - Agent queries MCP server, formats responses
4. **Zero Setup** - No Azure app registration, no credentials needed!

## 🚀 Quick Start (3 Commands)

```bash
# 1. Run the complete demo
./demo.sh

# 2. In another terminal, set up AI agent
cd ai-agent
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Run the AI agent
python agent.py
```

## 📁 What Was Created

### New Folders & Files

```
streamable-http-mcp/
├── ai-agent/                              # ✨ NEW - AI Agent
│   ├── agent.py                          # Main agent with LLM integration
│   ├── example_queries.py                # Example queries to test
│   ├── requirements.txt                  # Dependencies
│   ├── .env.example                      # Configuration template
│   ├── README.md                         # Project overview
│   └── USAGE.md                          # Detailed usage guide
│
├── application-mcp-server/
│   ├── main_mock.py                      # ✨ NEW - Mock server (no creds!)
│   ├── test_mock.py                      # ✨ NEW - Test script
│   ├── mock_data.py                      # ✨ NEW - Fake data
│   ├── setup_mock.sh                     # ✨ NEW - Setup script
│   ├── MOCK_SERVER.md                    # ✨ NEW - Mock server guide
│   └── src/application_mcp/
│       └── mock_graph.py                 # ✨ NEW - Mock MS Graph API
│
├── QUICKSTART.md                          # ✨ NEW - Quick start guide
├── ARCHITECTURE.md                        # ✨ NEW - System architecture
├── demo.sh                                # ✨ NEW - Complete demo script
└── SUMMARY.md                             # ✨ NEW - This file
```

## 🎬 How It Works

```
You ask: "Show me emails from john.doe@company.com"
    ↓
AI Agent (LLM decides to call list_emails tool)
    ↓
MCP Server (receives tool call)
    ↓
Mock Graph API (returns fake emails)
    ↓
AI Agent (formats response naturally)
    ↓
You see: "Here are the recent emails from John Doe's mailbox: ..."
```

## 📊 Mock Data Included

- **5 Sample Users**: John Doe, Jane Smith, Sarah Johnson, Mike Wilson, Emily Brown
- **Mock Emails**: 10+ email subjects with realistic content
- **3 Teams**: Engineering, Product, Marketing
- **Calendar Events**: Various meeting types
- **Realistic Metadata**: Timestamps, senders, recipients, etc.

## 💬 Example Conversation

```
You: List all users in the organization

Agent: Here are the users in your organization:

1. John Doe (john.doe@company.com)
   - Software Engineer, Engineering Department

2. Jane Smith (jane.smith@company.com)
   - Product Manager, Product Department

...

───────────────────────────────────────────────

You: Show me recent emails from john.doe@company.com

Agent: Here are the 5 most recent emails from John Doe's mailbox:

1. Weekly Team Sync (from Jane Smith)
   Date: 2024-01-18
   Preview: Hi team, Let's sync up this Friday...

2. Project Update: Q1 Goals (from Sarah Johnson)
   Date: 2024-01-17
   Preview: Hello, I wanted to share an update...

...

───────────────────────────────────────────────

You: What teams exist?

Agent: Here are all the teams in your organization:

1. Engineering Team - 12 members
   Software Engineering and Development

2. Product Team - 5 members
   Product Management and Strategy

3. Marketing Team - 8 members
   Marketing and Communications
```

## 🛠️ Tech Stack

- **MCP Server**: FastMCP 2.8+
- **AI Agent**: OpenAI GPT-4 or Anthropic Claude
- **API Server**: FastAPI + Uvicorn
- **Mock Data**: Python with realistic generators
- **Terminal UI**: Rich library for beautiful output

## 📚 Documentation

| File | Description |
|------|-------------|
| `QUICKSTART.md` | Get started in 5 minutes |
| `ARCHITECTURE.md` | Complete system diagram |
| `ai-agent/README.md` | AI agent overview |
| `ai-agent/USAGE.md` | How to use the agent |
| `application-mcp-server/MOCK_SERVER.md` | Mock server details |

## ✅ Testing

### Run Mock Server Tests
```bash
cd application-mcp-server
python main_mock.py  # In one terminal
python test_mock.py  # In another terminal
```

### Run AI Agent Examples
```bash
cd ai-agent
python example_queries.py
```

## 🔄 Mock vs Real Mode

| Feature | Mock Mode | Real Mode |
|---------|-----------|-----------|
| **Setup** | ✅ None needed | ❌ Azure app registration |
| **Credentials** | ✅ Not required | ❌ Client ID, Secret, Tenant |
| **Cost** | ✅ Free | 💰 API quotas |
| **Speed** | ⚡ Instant | 🐢 Network dependent |
| **Data** | 📦 Static/Fake | 🔄 Live/Real |
| **Internet** | ✅ Not needed | ❌ Required |
| **Use Case** | 🧪 Testing/Dev | 🚀 Production |

### Switching to Real Mode

When ready for production:

```bash
# 1. Set up Azure credentials
cd application-mcp-server
nano .env

# Add:
# AZURE_CLIENT_ID=your-client-id
# AZURE_CLIENT_SECRET=your-client-secret
# AZURE_TENANT_ID=your-tenant-id

# 2. Use real server instead of mock
python main.py  # Instead of main_mock.py
```

## 🎓 Learning Path

1. ✅ **Start Here** - Run mock server and test it
2. 🤖 Set up AI agent with your LLM API key
3. 💬 Try example queries
4. 🔧 Customize mock data for your use cases
5. 📊 Test complex multi-step queries
6. 🚀 When confident, switch to real Microsoft 365 data

## 🐛 Troubleshooting

### Server won't start
```bash
# Kill existing process on port 8001
lsof -ti:8001 | xargs kill -9

# Restart
python main_mock.py
```

### Agent can't connect
- Verify mock server is running: `curl http://localhost:8001/mcp`
- Check `MCP_SERVER_URL` in `ai-agent/.env`

### LLM errors
- Verify API key in `ai-agent/.env`
- Check you have API credits/quota
- Try a different model

### Import errors
```bash
# Reinstall dependencies
cd application-mcp-server && pip install -r requirements.txt
cd ../ai-agent && pip install -r requirements.txt
```

## 🔑 API Keys Needed

### For Mock MCP Server
- ✅ **None!** Works without any credentials

### For AI Agent
- ⚠️ **Required**: OpenAI API key OR Anthropic API key
- Get OpenAI key: https://platform.openai.com/api-keys
- Get Anthropic key: https://console.anthropic.com/

## 🎯 Next Steps

1. **Try the demo**: `./demo.sh`
2. **Read the quick start**: Open `QUICKSTART.md`
3. **Understand the architecture**: Open `ARCHITECTURE.md`
4. **Customize mock data**: Edit `application-mcp-server/mock_data.py`
5. **Build your own queries**: Experiment with the agent
6. **Deploy to production**: Switch to real mode

## 📞 Support

- Review `QUICKSTART.md` for common issues
- Check `ARCHITECTURE.md` to understand the system
- Look at `ai-agent/USAGE.md` for agent-specific help

## 🎉 You're Ready!

Everything is set up! Just run:

```bash
./demo.sh
```

And start chatting with your AI agent! 🚀

---

**Created for testing AI agents with MCP servers without Microsoft credentials**
