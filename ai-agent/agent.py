"""
AI Agent with MCP Server Integration

This agent uses an LLM (OpenAI or Anthropic) to understand user queries,
interact with the MCP server, and provide natural language responses.
"""
import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from fastmcp import Client
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Load environment variables
load_dotenv()

# Initialize console for rich output
console = Console()


@dataclass
class Message:
    """Represents a conversation message"""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class LLMProvider:
    """Base class for LLM providers"""
    
    async def complete(self, messages: List[Message], tools: List[Dict]) -> Dict[str, Any]:
        """Generate a completion with tool support"""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider"""
    
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    async def complete(self, messages: List[Message], tools: List[Dict]) -> Dict[str, Any]:
        """Generate completion using OpenAI"""
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            if msg.role == "tool":
                openai_messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id
                })
            else:
                message = {"role": msg.role, "content": msg.content}
                if msg.tool_calls:
                    message["tool_calls"] = msg.tool_calls
                openai_messages.append(message)
        
        # Make API call
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=tools if tools else None,
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "2000"))
        )
        
        return response.choices[0].message


class AnthropicProvider(LLMProvider):
    """Anthropic LLM Provider"""
    
    def __init__(self):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    async def complete(self, messages: List[Message], tools: List[Dict]) -> Dict[str, Any]:
        """Generate completion using Anthropic Claude"""
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "tool":
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content
                    }]
                })
            elif msg.tool_calls:
                # Assistant message with tool calls
                content = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                for tool_call in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "input": json.loads(tool_call["function"]["arguments"])
                    })
                anthropic_messages.append({
                    "role": "assistant",
                    "content": content
                })
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Convert tools to Anthropic format
        anthropic_tools = []
        if tools:
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
        
        # Make API call
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            system=system_message if system_message else "You are a helpful assistant.",
            messages=anthropic_messages,
            tools=anthropic_tools if anthropic_tools else None
        )
        
        # Convert response to OpenAI-like format for consistency
        result = {"content": "", "tool_calls": []}
        
        for content_block in response.content:
            if content_block.type == "text":
                result["content"] += content_block.text
            elif content_block.type == "tool_use":
                result["tool_calls"].append({
                    "id": content_block.id,
                    "type": "function",
                    "function": {
                        "name": content_block.name,
                        "arguments": json.dumps(content_block.input)
                    }
                })
        
        if not result["tool_calls"]:
            result["tool_calls"] = None
        
        return type('Response', (), result)


class AIAgent:
    """AI Agent that uses LLM to interact with MCP server"""
    
    def __init__(self, mcp_url: Optional[str] = None, llm_provider: Optional[str] = None):
        self.mcp_url = mcp_url or os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")
        provider = llm_provider or os.getenv("LLM_PROVIDER", "openai")
        
        # Initialize LLM provider
        if provider == "openai":
            self.llm = OpenAIProvider()
        elif provider == "anthropic":
            self.llm = AnthropicProvider()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
        
        self.mcp_client: Optional[Client] = None
        self.tools_schema: List[Dict] = []
        self.conversation_history: List[Message] = []
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))
    
    async def initialize(self):
        """Initialize the agent and connect to MCP server"""
        console.print("[cyan]🤖 Initializing AI Agent...[/cyan]")
        
        # Connect to MCP server
        self.mcp_client = Client(self.mcp_url)
        await self.mcp_client.__aenter__()
        
        console.print(f"[green]✅ Connected to MCP server at {self.mcp_url}[/green]")
        
        # Get available tools from MCP server
        await self._load_tools()
        
        # Set system prompt
        self.conversation_history.append(Message(
            role="system",
            content="""You are a helpful AI assistant with access to Microsoft 365 data through MCP tools.

Your capabilities include:
- Listing and searching users
- Reading emails from user mailboxes
- Getting user profiles
- Listing teams and team members
- Searching emails with various criteria

When a user asks a question:
1. Analyze what information is needed
2. Use the appropriate MCP tools to get the information
3. Provide clear, helpful responses based on the data
4. If you need to call multiple tools, do so systematically
5. Always be helpful and concise

Remember: You have application-level permissions, so you can access any user's data in the organization."""
        ))
        
        console.print(f"[green]✅ Loaded {len(self.tools_schema)} tools from MCP server[/green]")
        console.print("[cyan]🚀 Agent ready![/cyan]\n")
    
    async def _load_tools(self):
        """Load available tools from MCP server and convert to OpenAI format"""
        try:
            # Get the actual tools from the MCP client
            mcp_tools_response = await self.mcp_client.list_tools()
            
            # Extract tools list - it could be a list directly or have a .tools attribute
            if hasattr(mcp_tools_response, 'tools'):
                mcp_tools = mcp_tools_response.tools
            else:
                mcp_tools = mcp_tools_response
            
            # Convert to OpenAI function calling format
            self.tools_schema = []
            for tool in mcp_tools:
                tool_schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                self.tools_schema.append(tool_schema)
        
        except Exception as e:
            console.print(f"[red]Error loading tools: {e}[/red]")
            raise
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool and return the result"""
        try:
            console.print(f"[yellow]🔧 Executing tool: {tool_name}[/yellow]")
            console.print(f"[dim]   Arguments: {json.dumps(arguments, indent=2)}[/dim]")
            
            result = await self.mcp_client.call_tool(tool_name, arguments)
            
            # Extract text content
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return "Tool executed successfully but returned no content"
        
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            console.print(f"[red]❌ {error_msg}[/red]")
            return error_msg
    
    async def ask(self, question: str) -> str:
        """Ask the agent a question and get a response"""
        # Add user message to history
        self.conversation_history.append(Message(role="user", content=question))
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # Get LLM response
            response = await self.llm.complete(self.conversation_history, self.tools_schema)
            
            # Check if LLM wants to call tools
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Add assistant message with tool calls
                self.conversation_history.append(Message(
                    role="assistant",
                    content=response.content if hasattr(response, 'content') else "",
                    tool_calls=response.tool_calls
                ))
                
                # Execute each tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    tool_result = await self._execute_tool(tool_name, tool_args)
                    
                    # Add tool result to history
                    self.conversation_history.append(Message(
                        role="tool",
                        content=tool_result,
                        tool_call_id=tool_call.id,
                        name=tool_name
                    ))
                
                # Continue loop to get final response
                continue
            
            else:
                # No more tool calls, we have the final response
                final_response = response.content if hasattr(response, 'content') else str(response)
                
                # Add to history
                self.conversation_history.append(Message(
                    role="assistant",
                    content=final_response
                ))
                
                return final_response
        
        return "Maximum iterations reached. Unable to complete the request."
    
    async def close(self):
        """Close connections"""
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)
        console.print("[cyan]👋 Agent closed[/cyan]")


async def interactive_mode():
    """Run the agent in interactive CLI mode"""
    console.print(Panel.fit(
        "[bold cyan]AI Agent with MCP Server Integration[/bold cyan]\n"
        "Ask questions about your Microsoft 365 data!\n\n"
        "Type 'quit' or 'exit' to end the session.",
        title="🤖 AI Agent",
        border_style="cyan"
    ))
    
    agent = AIAgent()
    await agent.initialize()
    
    try:
        while True:
            # Get user input
            console.print("\n[bold green]You:[/bold green]", end=" ")
            user_input = input().strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                console.print("[cyan]Goodbye! 👋[/cyan]")
                break
            
            if not user_input:
                continue
            
            # Get agent response
            console.print("\n[bold cyan]Agent:[/bold cyan]")
            response = await agent.ask(user_input)
            
            # Display response with markdown formatting
            console.print(Markdown(response))
    
    except KeyboardInterrupt:
        console.print("\n[cyan]Interrupted. Goodbye! 👋[/cyan]")
    
    finally:
        await agent.close()


async def example_usage():
    """Example of programmatic usage"""
    agent = AIAgent()
    await agent.initialize()
    
    # Example queries
    queries = [
        "List all users in the organization",
        "Show me the 5 most recent emails from the first user",
    ]
    
    for query in queries:
        console.print(f"\n[bold green]Query:[/bold green] {query}")
        response = await agent.ask(query)
        console.print(f"[bold cyan]Response:[/bold cyan]\n{response}\n")
        console.print("-" * 80)
    
    await agent.close()


if __name__ == "__main__":
    # Run in interactive mode
    asyncio.run(interactive_mode())
    
    # Or run examples
    # asyncio.run(example_usage())
