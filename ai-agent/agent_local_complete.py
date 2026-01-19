"""
AI Agent with MCP Server Integration - Local LLM Version

This agent uses local/open-source LLM models (via Ollama or similar API)
to interact with the MCP server and respond to natural language queries.

Supported models:
- llama-3.3-70b-instruct (Best for general tasks, reasoning, and complex queries)
- codellama-13b-instruct (Best for code-related queries)
- llama-3-sqlcoder-8b (Best for SQL and database queries)
- llama-guard-3-8b (Best for content moderation)
- llama-prompt-guard-2-86m (Best for prompt injection detection)
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
import httpx

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


class LocalLLMProvider:
    """Local LLM Provider using Ollama or compatible API"""
    
    def __init__(self, model: str = "llama-3.3-70b-instruct", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        console.print(f"[cyan]🤖 Using local model: {model}[/cyan]")
        console.print(f"[dim]   API endpoint: {self.api_url} (single-prompt mode)[/dim]")
    
    async def complete(self, messages: List[Message], tools: List[Dict]) -> Dict[str, Any]:
        """Generate completion using local LLM with single prompt string"""
        
        # Build conversation parts
        conversation_parts = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "user":
                conversation_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                conversation_parts.append(f"Assistant: {msg.content}")
            elif msg.role == "tool":
                conversation_parts.append(f"Tool '{msg.name}' returned:\n{msg.content}")
        
        # Create enhanced prompt with tool information
        tools_description = self._format_tools_for_prompt(tools)
        
        # Build the complete single prompt string
        conversation = "\n\n".join(conversation_parts)
        
        if system_message and tools:
            prompt = f"""System: {system_message}

You have access to the following tools:

{tools_description}

When you need to use a tool, respond in this EXACT JSON format:
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "arguments": {{"param1": "value1", "param2": "value2"}}
    }}
  ],
  "reasoning": "Why you're calling this tool"
}}

If you don't need to call a tool, just respond normally to the user's question.
IMPORTANT: Only use tools when necessary. If you can answer from previous tool results, do so without calling more tools.

---

{conversation}

Assistant:"""
        else:
            prompt = f"""{system_message or 'You are a helpful assistant.'}

{conversation}

Assistant:"""
        
        # Make API call to local LLM
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
                            "num_predict": int(os.getenv("MAX_TOKENS", "2000"))
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                assistant_message = result.get("response", "")
                
                # Try to parse tool calls from response
                tool_calls = self._parse_tool_calls(assistant_message)
                
                if tool_calls:
                    return type('Response', (), {
                        'content': assistant_message,
                        'tool_calls': tool_calls
                    })
                else:
                    return type('Response', (), {
                        'content': assistant_message,
                        'tool_calls': None
                    })
                
            except httpx.RequestError as e:
                console.print(f"[red]Error connecting to local LLM: {e}[/red]")
                console.print(f"[yellow]Make sure Ollama is running: ollama serve[/yellow]")
                raise
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                raise
    
    def _format_tools_for_prompt(self, tools: List[Dict]) -> str:
        """Format tools for the prompt"""
        if not tools:
            return ""
        
        tools_text = []
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name", "")
            desc = func.get("description", "")
            params = func.get("parameters", {}).get("properties", {})
            
            params_text = ", ".join([f"{k}: {v.get('type', 'any')}" for k, v in params.items()])
            tools_text.append(f"- {name}({params_text}): {desc}")
        
        return "\n".join(tools_text)
    
    def _parse_tool_calls(self, content: str) -> Optional[List[Dict]]:
        """Parse tool calls from LLM response"""
        try:
            # Try to find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_str = content[start_idx:end_idx]
            parsed = json.loads(json_str)
            
            if "tool_calls" in parsed:
                # Convert to OpenAI-like format
                tool_calls = []
                for i, call in enumerate(parsed["tool_calls"]):
                    tool_calls.append({
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": call["name"],
                            "arguments": json.dumps(call["arguments"])
                        }
                    })
                return tool_calls
            
            return None
        except (json.JSONDecodeError, KeyError, ValueError):
            return None


class AIAgent:
    """AI Agent that uses Local LLM to interact with MCP server"""
    
    def __init__(
        self,
        mcp_url: Optional[str] = None,
        model: Optional[str] = None,
        llm_base_url: Optional[str] = None
    ):
        self.mcp_url = mcp_url or os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")
        model = model or os.getenv("LOCAL_MODEL", "llama-3.3-70b-instruct")
        llm_base_url = llm_base_url or os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
        
        # Initialize LLM provider
        self.llm = LocalLLMProvider(model=model, base_url=llm_base_url)
        
        self.mcp_client: Optional[Client] = None
        self.tools_schema: List[Dict] = []
        self.conversation_history: List[Message] = []
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))
    
    async def initialize(self):
        """Initialize the agent and connect to MCP server"""
        console.print("[cyan]🤖 Initializing AI Agent with Local LLM...[/cyan]")
        
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
        """Load available tools from MCP server and convert to function calling format"""
        try:
            # Get the actual tools from the MCP client
            mcp_tools_response = await self.mcp_client.list_tools()
            
            # Extract tools list - it could be a list directly or have a .tools attribute
            if hasattr(mcp_tools_response, 'tools'):
                mcp_tools = mcp_tools_response.tools
            else:
                mcp_tools = mcp_tools_response
            
            # Convert to function calling format
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
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])
                    
                    # Execute tool
                    tool_result = await self._execute_tool(tool_name, tool_args)
                    
                    # Add tool result to history
                    self.conversation_history.append(Message(
                        role="tool",
                        content=tool_result,
                        tool_call_id=tool_call['id'],
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
        "[bold cyan]AI Agent with Local LLM + MCP Server[/bold cyan]\n"
        "Ask questions about your Microsoft 365 data!\n\n"
        "Type 'quit' or 'exit' to end the session.",
        title="🤖 Local AI Agent",
        border_style="cyan"
    ))
    
    # Get model choice from user
    console.print("\n[yellow]Available models:[/yellow]")
    console.print("  1. llama-3.3-70b-instruct (Best for general tasks & reasoning)")
    console.print("  2. codellama-13b-instruct (Best for code-related queries)")
    console.print("  3. llama-3-sqlcoder-8b (Best for SQL/database queries)")
    console.print("\n[dim]Press Enter to use default (llama-3.3-70b-instruct)[/dim]")
    
    model_map = {
        "1": "llama-3.3-70b-instruct",
        "2": "codellama-13b-instruct",
        "3": "llama-3-sqlcoder-8b",
        "": "llama-3.3-70b-instruct"
    }
    
    choice = input("Choose model (1-3): ").strip()
    model = model_map.get(choice, "llama-3.3-70b-instruct")
    
    agent = AIAgent(model=model)
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
    agent = AIAgent(model="llama-3.3-70b-instruct")
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
