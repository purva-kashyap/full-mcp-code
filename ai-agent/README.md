# AI Agent with MCP Server Integration

This is an AI-powered agent that uses an LLM (OpenAI GPT-4 or Anthropic Claude) to interact with the Application MCP Server and respond to natural language queries.

## Features

- 🤖 Natural language understanding using LLM
- 🔧 Automatic tool selection and execution via MCP
- 💬 Conversational interface
- 🔄 Multi-turn conversations with context
- 📊 Support for complex queries requiring multiple tool calls

## Architecture

```
User Query → LLM (decides tools) → MCP Server (executes tools) → LLM (formats response) → User
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```env
# Choose your LLM provider (openai or anthropic)
LLM_PROVIDER=openai

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Configuration (if using Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8001/mcp
```

## Usage

### Interactive CLI Mode

```bash
python agent.py
```

Then type your questions:
```
You: List all users in the organization
Agent: Here are the users in your organization: ...

You: Show me recent emails from john@company.com
Agent: Here are the recent emails from John's mailbox: ...

You: What teams does Sarah belong to?
Agent: Sarah is a member of the following teams: ...
```

### Programmatic Usage

```python
from agent import AIAgent

async def main():
    agent = AIAgent()
    await agent.initialize()
    
    response = await agent.ask("List all users in the organization")
    print(response)
    
    await agent.close()
```

## Example Queries

- "List all users in the organization"
- "Show me the 5 most recent emails from john@company.com"
- "What teams exist in our organization?"
- "Get the members of the Marketing team"
- "Search for emails about 'project update' in jane@company.com's mailbox"
- "Show me Sarah's profile information"

## How It Works

1. **User Input**: User asks a question in natural language
2. **LLM Processing**: The LLM analyzes the query and determines which MCP tools to use
3. **Tool Execution**: The agent calls the appropriate MCP tools via the server
4. **Response Generation**: The LLM formats the tool results into a natural language response
5. **Context Management**: The conversation history is maintained for multi-turn interactions

## Configuration Options

### LLM Providers

- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet, Claude 3.5 Sonnet

### Agent Parameters

Edit `agent.py` to customize:
- `max_tokens`: Maximum response length
- `temperature`: Response creativity (0.0-1.0)
- `max_iterations`: Maximum tool calls per query

## Troubleshooting

### MCP Server Connection Issues
Ensure the MCP server is running:
```bash
cd ../application-mcp-server
python main.py
```

### LLM API Issues
- Verify your API key is correct
- Check your API quota/credits
- Ensure the model name is valid

## Advanced Features

### Streaming Responses (Future)
Support for streaming LLM responses for better UX

### Memory and Persistence
Save conversation history across sessions

### Custom Tools
Add your own custom tools to extend functionality
