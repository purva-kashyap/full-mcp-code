# Quick Start Guide - AI Agent with Mock MCP Server

Test your AI agent with realistic fake data - no Microsoft credentials needed!

## 🚀 One-Command Setup

```bash
cd application-mcp-server
./setup_mock.sh
```

This will:
- Install all dependencies for both MCP server and AI agent
- Create configuration files
- Show you next steps

## 📋 Manual Setup (Alternative)

### Step 1: Install Dependencies

```bash
# Install MCP server dependencies
cd application-mcp-server
pip install -r requirements.txt

# Install AI agent dependencies
cd ../ai-agent
pip install -r requirements.txt
```

### Step 2: Configure AI Agent

```bash
cd ai-agent
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY or ANTHROPIC_API_KEY
```

Example `.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
MCP_SERVER_URL=http://localhost:8001/mcp
```

### Step 3: Start Mock MCP Server

```bash
cd application-mcp-server
python main_mock.py
```

You should see:
```
🚀 Starting MOCK Microsoft 365 Application MCP Server...
   - FastAPI: http://localhost:8000
   - MCP endpoint: http://localhost:8001/mcp

⚠️  MOCK MODE ENABLED
   - No Azure credentials required
   - Returns realistic fake data
```

### Step 4: Test the Mock Server (Optional)

In a **new terminal**:
```bash
cd application-mcp-server
python test_mock.py
```

This will verify all tools are working with mock data.

### Step 5: Run the AI Agent

In a **new terminal**:
```bash
cd ai-agent
python agent.py
```

## 💬 Example Conversation

```
You: List all users in the organization

Agent: Here are the users in your organization:

1. John Doe (john.doe@company.com)
   - Job Title: Software Engineer
   - Department: Engineering

2. Jane Smith (jane.smith@company.com)
   - Job Title: Product Manager
   - Department: Product

3. Sarah Johnson (sarah.johnson@company.com)
   - Job Title: Senior Engineer
   - Department: Engineering

4. Mike Wilson (mike.wilson@company.com)
   - Job Title: Marketing Manager
   - Department: Marketing

5. Emily Brown (emily.brown@partner.com) - External Guest
   - Job Title: Consultant

---

You: Show me recent emails from john.doe@company.com

Agent: Here are the 5 most recent emails from John Doe's mailbox:

1. Subject: Weekly Team Sync
   From: Jane Smith
   Date: 2024-01-18T10:30:00Z
   Preview: Hi team, Let's sync up this Friday at 2pm...

2. Subject: Project Update: Q1 Goals
   From: Sarah Johnson
   Date: 2024-01-17T15:20:00Z
   Preview: Hello, I wanted to share an update on the project...

[...]

---

You: What teams exist in our organization?

Agent: Here are all the teams in your organization:

1. Engineering Team
   - Description: Software Engineering and Development
   - Members: 12
   - Visibility: Private

2. Product Team
   - Description: Product Management and Strategy
   - Members: 5
   - Visibility: Private

3. Marketing Team
   - Description: Marketing and Communications
   - Members: 8
   - Visibility: Public

---

You: Who are the members of the Engineering team?

Agent: The Engineering Team has the following members:

1. John Doe (john.doe@company.com)
   - Role: Member

2. Sarah Johnson (sarah.johnson@company.com)
   - Role: Member
```

## 🎯 Try These Queries

### User Management
- "List all users"
- "Show me the profile for john.doe@company.com"
- "Who are the external guests?"

### Email Operations
- "Show me the latest 5 emails from jane.smith@company.com"
- "Search for emails about 'project update'"
- "Get email details for the first email"

### Teams & Collaboration
- "What teams exist?"
- "Show me the members of the Product team"
- "List channels in the Engineering team"

### Calendar & Meetings
- "Show calendar events for john.doe@company.com"
- "List online meetings for jane.smith@company.com"

### Complex Queries
- "Find all teams and tell me how many members each has"
- "Show me the Engineering team members and their recent emails"
- "Search for urgent emails in all users' mailboxes"

## 🛠️ Customizing Mock Data

Edit `application-mcp-server/mock_data.py` to:

### Add More Users
```python
MOCK_USERS.append({
    "id": "user-006",
    "displayName": "Your Name",
    "mail": "your.name@company.com",
    # ... other fields
})
```

### Add More Email Subjects
```python
EMAIL_SUBJECTS.append("Your Custom Subject")
EMAIL_BODIES.append("Your custom email body...")
```

### Add More Teams
```python
MOCK_TEAMS.append({
    "id": "team-004",
    "displayName": "Your Team",
    "description": "Team description",
    # ...
})
```

## 🔄 Switching to Real Microsoft Data

Once you're ready to use real Microsoft 365 data:

1. **Set up Azure App Registration** (see main README.md)
2. **Configure environment variables**:
   ```bash
   cd application-mcp-server
   nano .env
   ```
   Add:
   ```env
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   AZURE_TENANT_ID=your-tenant-id
   ```
3. **Use the real server**:
   ```bash
   python main.py  # Instead of main_mock.py
   ```

## 🐛 Troubleshooting

### "Address already in use"
```bash
# Find and kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Restart mock server
python main_mock.py
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Cannot connect to MCP server"
- Ensure `main_mock.py` is running
- Check that port 8001 is accessible
- Verify MCP_SERVER_URL in ai-agent/.env

### AI Agent gives generic responses
- Check that your LLM API key is valid
- Ensure you have API credits/quota
- Try a simpler query first

### "Tool execution failed"
- Check mock server logs for errors
- Verify the tool name is correct
- Try running `test_mock.py` to verify server is working

## 📊 What's Different in Mock vs Real?

| Feature | Mock Mode | Real Mode |
|---------|-----------|-----------|
| Azure Credentials | ❌ Not needed | ✅ Required |
| Internet Required | ❌ No | ✅ Yes |
| API Costs | ❌ Free | 💰 Microsoft API quotas |
| Data Persistence | ❌ Static | ✅ Real-time |
| Response Speed | ⚡ Instant | 🐢 Network dependent |
| Use Case | Development/Testing | Production |

## 🎓 Learning Path

1. ✅ **Start here**: Test with mock data (you are here!)
2. 📚 Experiment with different queries
3. 🔧 Customize mock data to match your use cases
4. 🧪 Test your agent's capabilities
5. 🚀 Once confident, switch to real Microsoft data
6. 🌐 Deploy to production

## 📝 Terminal Layout Recommendation

```
┌─────────────────────────┬─────────────────────────┐
│  Terminal 1             │  Terminal 2             │
│  Mock MCP Server        │  AI Agent               │
│                         │                         │
│  $ python main_mock.py  │  $ python agent.py      │
│                         │                         │
│  [Server logs]          │  You: [Your queries]    │
│                         │  Agent: [Responses]     │
└─────────────────────────┴─────────────────────────┘
```

## ✅ Verification Checklist

Before starting, ensure:
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] LLM API key added to `ai-agent/.env`
- [ ] Mock server running on port 8001
- [ ] No firewall blocking localhost connections

## 🎉 You're Ready!

You now have:
- ✅ A working MCP server with mock data
- ✅ An AI agent that can query the MCP server
- ✅ Realistic test data to experiment with
- ✅ No Microsoft credentials needed

Start asking questions and see the AI agent in action! 🚀
