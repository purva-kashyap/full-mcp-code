# Microsoft 365 Email Reader - Web Application

Beautiful web interface for authenticating users and reading their Microsoft 365 emails.

## 📁 Folder Structure

```
web-app/
├── webapp.py                      # Flask app (local development)
├── webapp_k8s.py                  # Kubernetes-ready version
├── webapp_autoredirect_example.py # Auto-redirect example
├── Dockerfile.webapp              # Docker image
├── requirements-webapp.txt        # Python dependencies
├── WEBAPP.md                      # Web app documentation
├── KUBERNETES_WEBAPP.md           # K8s deployment guide
├── templates/
│   ├── index.html                 # Login page
│   └── dashboard.html             # Email dashboard
└── kubernetes/
    └── webapp-deployment.yaml     # K8s manifests
```

## 🚀 Quick Start (Local Development)

### Prerequisites
- MCP server running on port 8001
- Callback server running on port 8000

### Run Web App

```bash
cd web-app

# Install dependencies
pip install -r requirements-webapp.txt

# Run local version
python3 webapp.py

# Open browser
open http://localhost:5000
```

## 🐳 Docker

```bash
# Build
docker build -f Dockerfile.webapp -t ms365-webapp .

# Run
docker run -p 5000:5000 \
  -e MCP_SERVER_URL=http://host.docker.internal:8001/mcp/ \
  ms365-webapp
```

## ☸️ Kubernetes

See [KUBERNETES_WEBAPP.md](KUBERNETES_WEBAPP.md) for complete deployment guide.

```bash
# Deploy
kubectl apply -f kubernetes/webapp-deployment.yaml

# Check status
kubectl get pods -l app=webapp
```

## 📚 Documentation

- **[WEBAPP.md](WEBAPP.md)** - Complete web app guide
- **[KUBERNETES_WEBAPP.md](KUBERNETES_WEBAPP.md)** - K8s deployment
- **Parent README** - `../README.md` for overall project

## 🔗 Related Services

This web app connects to:
- **MCP Server** (`../microsoft-mcp/`) - Backend API
- **Callback Server** (`../callback-server/`) - OAuth handling

## 🎨 Features

✅ Beautiful gradient UI  
✅ OAuth popup authentication  
✅ Real-time callback polling  
✅ Session management  
✅ Email dashboard (inbox, sent, drafts)  
✅ Multi-user support  
✅ Kubernetes-ready  

## 🔧 Configuration

### Local Development (webapp.py)
- Hardcoded `http://0.0.0.0:8001/mcp/`
- In-memory sessions
- Debug mode enabled

### Kubernetes (webapp_k8s.py)
- Service discovery via env vars
- Redis session storage
- Production-ready with Gunicorn

## 📝 License

MIT
