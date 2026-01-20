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
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from fastmcp import Client
import httpx
import uvicorn

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Agent Chat")

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str


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
        print(f"[Init] Using local model: {model} at {self.api_url}")
    
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

When you need to use a tool, respond ONLY with JSON in this EXACT format (no other text):
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "arguments": {{"param1": "value1", "param2": "value2"}}
    }}
  ]
}}

CRITICAL RULES:
1. If you need to call a tool, respond with ONLY the JSON above - no explanations, no other text
2. After tool results are provided, you can respond normally to answer the user's question
3. Use information from previous tool results (like meeting IDs, user emails) in subsequent tool calls
4. When user refers to "the first meeting", "that meeting", etc., extract the ID from previous tool results
5. Only call tools when you don't already have the needed information

Examples:
User: "List meetings for john@example.com"
You: {{"tool_calls": [{{"name": "list_online_meetings", "arguments": {{"user_email": "john@example.com"}}}}]}}

Tool returns: "Meeting 1: ID=abc123, Title=Standup. Meeting 2: ID=def456, Title=Review"
User: "Get transcript for the first meeting"
You: {{"tool_calls": [{{"name": "get_online_meeting_transcript", "arguments": {{"user_email": "john@example.com", "meeting_id": "abc123"}}}}]}}

---

{conversation}"""
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
                print(f"Error connecting to local LLM: {e}")
                print("Make sure your LLM server is running")
                raise
            except Exception as e:
                print(f"Error: {e}")
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
        """Parse tool calls from LLM response with improved extraction"""
        try:
            # Clean up the content - remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
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
                    # Handle both formats: {"name": ..., "arguments": ...} and others
                    if isinstance(call, dict):
                        tool_name = call.get("name") or call.get("function")
                        tool_args = call.get("arguments") or call.get("args") or {}
                        
                        tool_calls.append({
                            "id": f"call_{i}",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args) if isinstance(tool_args, dict) else tool_args
                            }
                        })
                return tool_calls if tool_calls else None
            
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[Debug] Failed to parse tool calls: {e}")
            print(f"[Debug] Content was: {content[:300]}...")  # Print first 300 chars for debugging
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
        print("Initializing AI Agent with Local LLM...")
        
        # Connect to MCP server
        self.mcp_client = Client(self.mcp_url)
        await self.mcp_client.__aenter__()
        
        print(f"Connected to MCP server at {self.mcp_url}")
        
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
        
        print(f"Loaded {len(self.tools_schema)} tools from MCP server")
        print("Agent ready!\n")
    
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
            print(f"Error loading tools: {e}")
            raise
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool and return the result"""
        try:
            print(f"Executing tool: {tool_name}")
            print(f"Arguments: {json.dumps(arguments, indent=2)}")
            
            result = await self.mcp_client.call_tool(tool_name, arguments)
            
            # Extract text content
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return "Tool executed successfully but returned no content"
        
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            print(f"Error: {error_msg}")
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
        print("Agent closed")


# Global agent instance
agent_instance: Optional[AIAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent_instance
    model = os.getenv("LOCAL_MODEL", "llama-3.3-70b-instruct")
    agent_instance = AIAgent(model=model)
    await agent_instance.initialize()
    print("Web server started and agent initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global agent_instance
    if agent_instance:
        await agent_instance.close()


@app.get("/", response_class=HTMLResponse)
async def get_chat_ui():
    """Serve the chat UI"""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>AI Agent Chat</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            height: 90vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #0a1929 0%, #1a2332 100%);
            color: white;
            padding: 24px;
            border-radius: 16px 16px 0 0;
            text-align: center;
        }
        .header h1 {
            font-size: 24px;
            margin-bottom: 8px;
        }
        .header p {
            font-size: 14px;
            opacity: 0.9;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            background: #f7f8fa;
        }
        .message {
            margin-bottom: 16px;
            display: flex;
            align-items: flex-start;
        }
        .message.user {
            justify-content: flex-end;
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 16px;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #0a1929 0%, #1a2332 100%);
            color: white;
        }
        .message.agent .message-content {
            background: white;
            color: #333;
            border: 1px solid #e1e8ed;
        }
        .message-label {
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 4px;
            opacity: 0.7;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e1e8ed;
            border-radius: 0 0 16px 16px;
        }
        .input-wrapper {
            display: flex;
            gap: 12px;
        }
        #userInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e1e8ed;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        #userInput:focus {
            border-color: #2a5298;
        }
        button {
            padding: 12px 28px;
            background: linear-gradient(135deg, #0a1929 0%, #1a2332 100%);
            color: white;
            border: none;
            border-radius: 24px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 60, 114, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .reset-btn {
            margin-left: 8px;
            padding: 12px 20px;
            background: #6c757d;
        }
        .reset-btn:hover {
            box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4);
        }
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 16px;
            width: fit-content;
        }
        .typing-indicator.active {
            display: block;
        }
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background: #1a2332;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }
        .error {
            color: #dc3545;
            padding: 12px;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Agent Chat</h1>
            <p>Ask questions about your Microsoft 365 data</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message agent">
                <div>
                    <div class="message-label">Agent</div>
                    <div class="message-content">Hello! I'm your AI assistant with access to Microsoft 365 data through MCP tools. How can I help you today?</div>
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-wrapper">
                <input type="text" id="userInput" placeholder="Type your message here..." />
                <button id="sendBtn" onclick="sendMessage()">Send</button>
                <button class="reset-btn" onclick="resetChat()">Reset</button>
            </div>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');

        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;

            // Add user message
            addMessage('user', message);
            userInput.value = '';
            sendBtn.disabled = true;

            // Show typing indicator
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator active';
            typingDiv.innerHTML = '<span></span><span></span><span></span>';
            chatMessages.appendChild(typingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                // Remove typing indicator
                typingDiv.remove();

                if (data.status === 'success') {
                    addMessage('agent', data.response);
                } else {
                    addMessage('agent', 'Sorry, an error occurred: ' + (data.response || 'Unknown error'));
                }
            } catch (error) {
                typingDiv.remove();
                addMessage('agent', 'Sorry, I encountered an error: ' + error.message);
            }

            sendBtn.disabled = false;
            userInput.focus();
        }

        function addMessage(sender, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const label = sender === 'user' ? 'You' : 'Agent';
            messageDiv.innerHTML = `
                <div>
                    <div class="message-label">${label}</div>
                    <div class="message-content">${escapeHtml(content)}</div>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        async function resetChat() {
            if (!confirm('Are you sure you want to reset the conversation?')) return;

            try {
                const response = await fetch('/reset', {
                    method: 'POST',
                });

                const data = await response.json();
                
                if (data.status === 'success') {
                    // Clear chat
                    chatMessages.innerHTML = `
                        <div class="message agent">
                            <div>
                                <div class="message-label">Agent</div>
                                <div class="message-content">Conversation reset. How can I help you?</div>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                alert('Error resetting conversation: ' + error.message);
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Focus input on load
        window.onload = () => userInput.focus();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages"""
    try:
        if not agent_instance:
            return ChatResponse(
                response="Agent not initialized",
                status="error"
            )
        
        response = await agent_instance.ask(request.message)
        return ChatResponse(
            response=response,
            status="success"
        )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return ChatResponse(
            response=str(e),
            status="error"
        )


@app.post("/reset")
async def reset_conversation():
    """Reset the conversation history"""
    try:
        global agent_instance
        if agent_instance:
            # Reset conversation history but keep system message
            system_msg = agent_instance.conversation_history[0] if agent_instance.conversation_history else None
            agent_instance.conversation_history = [system_msg] if system_msg else []
        
        return JSONResponse(
            content={"status": "success", "message": "Conversation reset"}
        )
    except Exception as e:
        print(f"Error resetting conversation: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


if __name__ == "__main__":
    # Run the web server
    import uvicorn
    print("Starting AI Agent Chat Web Server...")
    print("Open your browser to http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
