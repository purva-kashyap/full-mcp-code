# Microsoft 365 MCP Server

Production-ready MCP (Model Context Protocol) server for Microsoft 365 / Microsoft Graph API with separated OAuth callback service.

## 📁 Project Structure

```
streamable-http-mcp/
├── microsoft-mcp/          # Main MCP Server
│   ├── src/                # Source code
│   ├── main.py             # Server entry point
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # MCP server Docker image
│   └── kubernetes/         # K8s manifests for MCP server
│
└── callback-server/        # OAuth Callback Service (Separate)
    ├── oauth_callback_server.py  # Standalone callback server
    ├── Dockerfile                 # Callback server Docker image
    ├── deployment.yaml            # K8s manifest
    └── README.md                  # Callback server docs
```

## 🎯 Why Separate Servers?

### Local Development
- **Single Process**: MCP server includes built-in callback handler
- **Easy Testing**: No separate deployment needed
- **Fast Iteration**: Quick start with `python3 main.py`

### Production / Kubernetes
- **Scalability**: MCP server can scale horizontally
- **Separation of Concerns**: Auth handling isolated from business logic
- **Resilience**: Services can be updated/scaled independently
- **Security**: Callback service can have different security policies

## 🚀 Quick Start

### Local Development (Built-in Callback)

```bash
cd microsoft-mcp

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Azure AD credentials

# Run (includes built-in callback server)
python3 main.py
```

Servers start on:
- MCP Server: `http://localhost:8001`
- OAuth Callback: `http://localhost:8000` (built-in)

### Kubernetes (Separate Services)

```bash
# Deploy OAuth Callback Service
cd callback-server
kubectl apply -f deployment.yaml

# Deploy MCP Server
cd ../microsoft-mcp
kubectl apply -f kubernetes/
```

See individual READMEs for detailed instructions:
- [MCP Server Setup](microsoft-mcp/SETUP.md)
- [MCP Server Deployment](microsoft-mcp/DEPLOYMENT.md)
- [Callback Server](callback-server/README.md)

## 🏗️ Architecture

### Local Development
```
┌─────────────────────────┐
│   microsoft-mcp         │
│   (main.py)             │
│                         │
│  ┌───────────────────┐  │
│  │  MCP Server       │  │
│  │  Port: 8001       │  │
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │  OAuth Callback   │  │
│  │  Port: 8000       │  │
│  │  (built-in)       │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

### Kubernetes Production
```
                ┌─────────────┐
                │   Ingress   │
                │ (NGINX/ALB) │
                └──────┬──────┘
                       │
        ┌──────────────┴─────────────┐
        │                            │
┌───────▼────────┐          ┌────────▼────────┐
│ callback-server│          │  microsoft-mcp  │
│                │          │                 │
│ OAuth Callback │◄────API──┤   MCP Server    │
│  Port: 8000    │          │   Port: 8001    │
│  Replicas: 1   │          │   Replicas: N   │
└────────────────┘          └─────────────────┘
```

## 🔧 Configuration

### MCP Server Environment Variables

| Variable | Local | Kubernetes | Description |
|----------|-------|------------|-------------|
| `MICROSOFT_MCP_CLIENT_ID` | Required | ConfigMap | Azure AD Client ID |
| `MICROSOFT_MCP_CLIENT_SECRET` | Required | Secret | Azure AD Client Secret |
| `MICROSOFT_MCP_ENABLE_CALLBACK_SERVER` | `true` | `false` | Enable built-in callback |
| `MICROSOFT_MCP_REDIRECT_URI` | `http://localhost:8000/callback` | `https://yourdomain.com/oauth/callback` | OAuth redirect |
| `MICROSOFT_MCP_OAUTH_CALLBACK_API_URL` | - | `http://oauth-callback-service:8000/api/callback/{state}` | External callback API |

### Callback Server Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OAUTH_CALLBACK_HOST` | `0.0.0.0` | Host to bind to |
| `OAUTH_CALLBACK_PORT` | `8000` | Port to listen on |

## 📦 Available MCP Tools

1. **Authentication**
   - `list_accounts` - List authenticated accounts
   - `authenticate_account` - Start OAuth flow
   - `wait_for_callback` - Wait for OAuth callback
   - `complete_authentication` - Complete auth

2. **User Profile**
   - `get_user_profile` - Get user profile info

3. **Email**
   - `list_emails` - List emails from folders
   - `get_email` - Get email details
   - `search_emails` - Search emails

## 🐳 Docker Images

### Build Both Services

```bash
# Build OAuth Callback Server
cd callback-server
docker build -t oauth-callback-server:latest .

# Build MCP Server
cd ../microsoft-mcp
docker build -t mcp-server:latest .
```

### Run with Docker Compose

```yaml
version: '3.8'
services:
  oauth-callback:
    build: ./callback-server
    ports:
      - "8000:8000"
  
  mcp-server:
    build: ./microsoft-mcp
    ports:
      - "8001:8001"
    environment:
      - MICROSOFT_MCP_ENABLE_CALLBACK_SERVER=false
      - MICROSOFT_MCP_OAUTH_CALLBACK_API_URL=http://oauth-callback:8000/api/callback/{state}
    env_file:
      - microsoft-mcp/.env
    depends_on:
      - oauth-callback
```

## 📚 Documentation

- **[MCP Server Setup Guide](microsoft-mcp/SETUP.md)** - Local development
- **[Deployment Guide](microsoft-mcp/DEPLOYMENT.md)** - Kubernetes deployment
- **[Callback Server](callback-server/README.md)** - Standalone callback service
- **[Kubernetes Configuration](microsoft-mcp/kubernetes/README.md)** - K8s details

## 🔐 Azure AD Setup

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Create new registration:
   - Name: `microsoft-mcp-server`
   - Supported account types: Choose based on your needs
4. Note the **Application (client) ID**
5. Create **Client Secret** under Certificates & secrets
6. Add **Redirect URI** under Authentication:
   - Local: `http://localhost:8000/callback`
   - Production: `https://yourdomain.com/oauth/callback`
7. Add **API Permissions**:
   - Microsoft Graph > Delegated permissions
   - Add: `User.Read`, `Mail.Read`

## 🧪 Testing

### Test Callback Server Separately
```bash
cd callback-server
python3 oauth_callback_server.py

# In another terminal
curl http://localhost:8000/health
```

### Test MCP Server
```bash
cd microsoft-mcp
python3 main.py

# In another terminal
python3 simple_client.py
```

### Test Full Flow
```bash
# Terminal 1: Callback server
cd callback-server && python3 oauth_callback_server.py

# Terminal 2: MCP server (configured for external callback)
cd microsoft-mcp
export MICROSOFT_MCP_ENABLE_CALLBACK_SERVER=false
export MICROSOFT_MCP_OAUTH_CALLBACK_API_URL=http://localhost:8000/api/callback/{state}
python3 main.py

# Terminal 3: Client
cd microsoft-mcp && python3 simple_client.py
```

## 📝 Requirements

- Python 3.12+
- Azure AD application with client ID and secret
- For K8s: Kubernetes 1.20+, nginx-ingress, cert-manager

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing structure
- Both local and K8s modes are tested
- Documentation is updated

## 📄 License

MIT License

## 🔗 Related Projects

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP framework
- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/overview) - Microsoft 365 API
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python) - Microsoft auth library
