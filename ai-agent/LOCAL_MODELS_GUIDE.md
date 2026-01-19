# Local LLM Models Guide

## Available Models & Best Use Cases

### 1. **llama-3.3-70b-instruct** ⭐ RECOMMENDED
**Best for:** General-purpose tasks, complex reasoning, multi-step queries

**Use cases:**
- Understanding natural language questions
- Multi-step reasoning (e.g., "Find all teams and show members of the Engineering team")
- General Q&A about Microsoft 365 data
- Conversational interactions
- Complex decision-making

**Pros:**
- Best overall performance
- Strong reasoning capabilities
- Good at understanding context
- Handles complex queries well

**Cons:**
- Requires more memory/compute
- Slower than smaller models

**Example queries:**
```
- "Find all users in the organization and tell me how many are in Engineering"
- "Show me recent emails from john.doe@company.com and summarize the topics"
- "What teams exist and who are their key members?"
```

---

### 2. **codellama-13b-instruct**
**Best for:** Code-related queries, technical documentation

**Use cases:**
- Understanding code in email bodies
- Technical discussions
- API-related queries
- Code review comments
- Technical documentation

**Pros:**
- Specialized for code understanding
- Good at technical terminology
- Faster than llama-3.3-70b

**Cons:**
- Not as good for general conversation
- May be too technical for simple queries

**Example queries:**
```
- "Search for emails about 'API implementation' in the Engineering team"
- "Find code review comments in recent emails"
- "Show me technical documentation shared in Teams channels"
```

---

### 3. **llama-3-sqlcoder-8b**
**Best for:** SQL and database-related queries (less relevant for M365 data)

**Use cases:**
- If you need to generate SQL queries
- Database-related discussions
- Structured data queries

**Pros:**
- Excellent for SQL generation
- Fast and efficient
- Small memory footprint

**Cons:**
- Not ideal for general Microsoft 365 queries
- Limited reasoning for complex tasks
- May struggle with non-database topics

**Example queries:**
```
- "How would I query the user database to find all emails?"
- "Help me understand the data structure of teams"
```

⚠️ **Note:** This model is less useful for your use case since you're working with Microsoft 365 data via APIs, not SQL databases.

---

### 4. **llama-guard-3-8b**
**Best for:** Content moderation and safety checks

**Use cases:**
- Filtering inappropriate content
- Safety checks before displaying emails
- Content moderation in team channels

**Pros:**
- Specialized for safety
- Fast inference
- Good at detecting problematic content

**Cons:**
- Not suitable as a primary agent
- Limited general-purpose capabilities

**Example usage:**
```python
# Use as a safety layer before displaying content
is_safe = await guard_model.check_safety(email_content)
```

---

### 5. **llama-prompt-guard-2-86m**
**Best for:** Detecting prompt injection attacks

**Use cases:**
- Security layer for user inputs
- Preventing prompt injection
- Input validation

**Pros:**
- Very fast (tiny model)
- Specialized for security
- Low resource usage

**Cons:**
- Not suitable as a primary agent
- Very limited capabilities

**Example usage:**
```python
# Use before processing user queries
is_injection = await prompt_guard.detect_injection(user_query)
```

---

## Recommendations by Scenario

### For Your AI Agent (Microsoft 365 Data)

#### **Best Choice: llama-3.3-70b-instruct** ✅
This is the best model for your use case because:
- Excellent at understanding natural language questions
- Can reason through multi-step queries
- Handles function calling simulation well
- Good at formatting responses

#### **Alternative: codellama-13b-instruct** 🔧
Use this if:
- Most queries are technical in nature
- You need faster responses
- Limited compute resources

#### **Not Recommended for Primary Agent:**
- ❌ llama-3-sqlcoder-8b (too specialized for SQL)
- ❌ llama-guard-3-8b (safety only)
- ❌ llama-prompt-guard-2-86m (security only)

---

## Setup Instructions

### 1. Install Ollama

```bash
# macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai
```

### 2. Pull Models

```bash
# Recommended model
ollama pull llama3.3:70b-instruct

# Alternative models
ollama pull codellama:13b-instruct
ollama pull sqlcoder:8b
```

### 3. Start Ollama Server

```bash
ollama serve
```

### 4. Configure the Agent

```bash
cd ai-agent
cp .env.local.example .env.local

# Edit .env.local
nano .env.local
```

Set:
```env
LOCAL_MODEL=llama-3.3-70b-instruct
LOCAL_LLM_BASE_URL=http://localhost:11434
```

### 5. Run the Local Agent

```bash
# Make sure mock MCP server is running
cd ../application-mcp-server
python main_mock.py

# In another terminal, run local agent
cd ../ai-agent
python agent_local.py
```

---

## Performance Comparison

| Model | Speed | Memory | Reasoning | Code | General |
|-------|-------|--------|-----------|------|---------|
| llama-3.3-70b | ⭐⭐ | High | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| codellama-13b | ⭐⭐⭐⭐ | Medium | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| sqlcoder-8b | ⭐⭐⭐⭐⭐ | Low | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| llama-guard | ⭐⭐⭐⭐⭐ | Low | - | - | - |
| prompt-guard | ⭐⭐⭐⭐⭐ | Tiny | - | - | - |

---

## Model Naming in Ollama

The models might have different names in Ollama. Here's the mapping:

| Your Model | Ollama Model Name |
|------------|-------------------|
| llama-3.3-70b-instruct | `llama3.3:70b-instruct` |
| codellama-13b-instruct | `codellama:13b-instruct` |
| llama-3-sqlcoder-8b | `sqlcoder:8b` |
| llama-guard-3-8b | `llama-guard3:8b` |
| llama-prompt-guard-2-86m | Not available in Ollama |

Update `agent_local.py` or `.env.local` accordingly if needed.

---

## Testing

Try these queries with different models:

### Test with llama-3.3-70b-instruct:
```
List all users in the organization
Show me recent emails from john.doe@company.com
What teams exist and how many members does each have?
Find all Engineering team members and their recent emails
```

### Test with codellama-13b-instruct:
```
Search for emails about 'code review' or 'pull request'
Find technical discussions in the Engineering team
Show me emails with code snippets or technical content
```

---

## Troubleshooting

### Model not found
```bash
# List available models
ollama list

# Pull the model
ollama pull llama3.3:70b-instruct
```

### Slow responses
- Use a smaller model (codellama-13b-instruct)
- Reduce MAX_TOKENS in .env.local
- Check CPU/GPU usage

### Ollama not running
```bash
# Start Ollama
ollama serve

# Or on macOS, it should auto-start
```

---

## Summary

**For your Microsoft 365 AI Agent:**
1. **Primary**: Use `llama-3.3-70b-instruct` for best results
2. **Fallback**: Use `codellama-13b-instruct` if you need speed
3. **Avoid**: sqlcoder, llama-guard, prompt-guard for primary agent

The local agent is now ready to use with these models! 🚀
