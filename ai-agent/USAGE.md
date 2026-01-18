# AI Agent Usage Guide

## Quick Start

1. **Setup Environment**
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Start MCP Server**
Make sure the application-mcp-server is running:
```bash
cd ../application-mcp-server
python main.py
```

4. **Run the Agent**
```bash
python agent.py
```

## Usage Modes

### Interactive CLI Mode (Default)

Simply run the agent and start asking questions:

```bash
python agent.py
```

Example session:
```
🤖 AI Agent with MCP Server Integration
Ask questions about your Microsoft 365 data!

You: List all users in the organization

Agent: Here are the users in your organization:

1. John Doe (john.doe@company.com)
   - Job Title: Software Engineer
   - Department: Engineering

2. Jane Smith (jane.smith@company.com)
   - Job Title: Product Manager
   - Department: Product

...

You: Show me recent emails from john.doe@company.com

Agent: Here are the 5 most recent emails from John Doe's mailbox:

1. Subject: Weekly Team Sync
   From: sarah@company.com
   Date: 2024-01-15
   Preview: Hi team, let's sync up on Friday...

...
```

### Programmatic Usage

Use the agent in your own Python scripts:

```python
import asyncio
from agent import AIAgent

async def main():
    # Initialize agent
    agent = AIAgent()
    await agent.initialize()
    
    # Ask questions
    response = await agent.ask("List all users")
    print(response)
    
    response = await agent.ask("Show me the latest emails")
    print(response)
    
    # Clean up
    await agent.close()

asyncio.run(main())
```

### Run Example Queries

Test the agent with predefined examples:

```bash
python example_queries.py
```

## Configuration

### Environment Variables

Edit `.env` to configure:

```env
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai

# OpenAI Settings
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Settings
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# MCP Server
MCP_SERVER_URL=http://localhost:8001/mcp

# Agent Behavior
MAX_ITERATIONS=5        # Max tool calls per query
TEMPERATURE=0.7         # Response creativity (0-1)
MAX_TOKENS=2000        # Max response length
```

### Choosing an LLM Provider

**OpenAI (GPT-4)**
- Pros: Excellent function calling, fast, well-documented
- Cons: Costs can add up with heavy usage
- Best for: Production use, complex reasoning

**Anthropic (Claude)**
- Pros: Large context window, strong reasoning, competitive pricing
- Cons: Slightly different API patterns
- Best for: Long conversations, detailed analysis

## Example Queries

### User Management
```
- "List all users in the organization"
- "How many users do we have?"
- "Show me user profiles"
- "Find external guest users"
```

### Email Operations
```
- "Show me recent emails from john@company.com"
- "Search for emails about 'project update'"
- "Get unread emails from the CEO's mailbox"
- "Find emails with attachments"
```

### Teams Operations
```
- "List all Microsoft Teams"
- "Who are the members of the Engineering team?"
- "Show me all teams and their sizes"
```

### Complex Queries
```
- "Find the Marketing team and list all members' recent emails"
- "Search for urgent emails across all users"
- "Get the profile of the first user and their latest emails"
```

## How It Works

### Request Flow

1. **User Input**: You ask a natural language question
   ```
   "Show me recent emails from john@company.com"
   ```

2. **LLM Analysis**: The LLM determines needed actions
   ```
   Tool needed: list_emails
   Arguments: {"user_email": "john@company.com", "limit": 5}
   ```

3. **Tool Execution**: Agent calls MCP server
   ```python
   result = await mcp_client.call_tool("list_emails", {...})
   ```

4. **Response Generation**: LLM formats the result
   ```
   "Here are the 5 most recent emails from John's mailbox:
   1. Subject: Team Meeting..."
   ```

### Multi-Step Reasoning

The agent can chain multiple tool calls:

```
User: "Find the Engineering team and show recent emails from its members"

Step 1: list_teams() → Find Engineering team
Step 2: get_team_members(team_id) → Get member list
Step 3: list_emails(member1) → Get emails
Step 4: Format response with all information
```

## Troubleshooting

### "Cannot connect to MCP server"
- Ensure MCP server is running: `cd ../application-mcp-server && python main.py`
- Check MCP_SERVER_URL in .env

### "Invalid API key"
- Verify your API key in .env
- Check if you have credits/quota remaining
- Ensure you're using the correct provider (openai vs anthropic)

### "Tool execution failed"
- Check that MCP server has proper Azure credentials
- Verify the tool exists: check available tools with "list all available tools"
- Check MCP server logs for errors

### Slow responses
- Reduce MAX_TOKENS in .env
- Use faster models (gpt-3.5-turbo instead of gpt-4)
- Reduce TEMPERATURE for more deterministic responses

## Advanced Usage

### Custom System Prompt

Modify the system prompt in `agent.py` to change behavior:

```python
self.conversation_history.append(Message(
    role="system",
    content="Your custom instructions here..."
))
```

### Adding Conversation Memory

Save conversation history to a file:

```python
import json

# After each interaction
with open('conversation.json', 'w') as f:
    json.dump([
        {"role": msg.role, "content": msg.content}
        for msg in agent.conversation_history
    ], f)
```

### Integration with Web Apps

Use the agent in a Flask/FastAPI web app:

```python
from fastapi import FastAPI
from agent import AIAgent

app = FastAPI()
agent = AIAgent()

@app.on_event("startup")
async def startup():
    await agent.initialize()

@app.post("/ask")
async def ask_question(question: str):
    response = await agent.ask(question)
    return {"response": response}
```

## Best Practices

1. **Be Specific**: More specific queries get better results
   - ❌ "Show emails"
   - ✅ "Show the 5 most recent emails from john@company.com"

2. **Use Natural Language**: The agent understands conversational queries
   - ✅ "Who's in the Marketing team?"
   - ✅ "Can you show me Sarah's recent emails?"

3. **Multi-turn Conversations**: Build on previous context
   - You: "List all teams"
   - Agent: [shows teams]
   - You: "Show members of the first one"

4. **Error Handling**: If a query fails, rephrase it
   - Try being more specific
   - Check if the resource exists
   - Verify the MCP server is running

## Next Steps

- Create a web interface for the agent
- Add conversation persistence
- Implement streaming responses
- Add more sophisticated error handling
- Create specialized agents for specific tasks
