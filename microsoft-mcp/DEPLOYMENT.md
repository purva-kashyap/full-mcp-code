# Deployment Guide

## Overview

The Microsoft MCP Server can be deployed in two modes:

1. **Local Development** - Single server with built-in callback
2. **Kubernetes Production** - Separate OAuth callback service

## Local Development Setup

### Using Built-in Callback Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run the server
python3 main.py
```

The server will start:
- MCP Server on port 8001
- OAuth Callback on port 8000 (built-in)

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured
- Docker registry access
- Domain name with TLS certificate

### 1. Build and Push Docker Images

```bash
# Build OAuth Callback Server
docker build -f Dockerfile.callback -t your-registry/oauth-callback-server:latest .
docker push your-registry/oauth-callback-server:latest

# Build MCP Server
docker build -t your-registry/mcp-server:latest .
docker push your-registry/mcp-server:latest
```

### 2. Update Azure AD App Registration

In Azure Portal, update your app's redirect URI:
```
https://yourdomain.com/oauth/callback
```

### 3. Create Kubernetes Secrets and ConfigMaps

```bash
# Create ConfigMap
kubectl create configmap mcp-config \
  --from-literal=MICROSOFT_MCP_CLIENT_ID=your-client-id \
  --from-literal=MICROSOFT_MCP_TENANT_ID=consumers

# Create Secret
kubectl create secret generic mcp-secret \
  --from-literal=MICROSOFT_MCP_CLIENT_SECRET=your-client-secret
```

### 4. Update Kubernetes Manifests

Edit `kubernetes/mcp-server-deployment.yaml`:
- Update `image:` with your registry
- Update `MICROSOFT_MCP_REDIRECT_URI` with your domain

Edit `kubernetes/oauth-callback-deployment.yaml`:
- Update `image:` with your registry

Edit `kubernetes/ingress.yaml`:
- Update `host:` with your domain

### 5. Deploy

```bash
# Deploy OAuth Callback Service
kubectl apply -f kubernetes/oauth-callback-deployment.yaml

# Deploy MCP Server
kubectl apply -f kubernetes/mcp-server-deployment.yaml

# Deploy Ingress
kubectl apply -f kubernetes/ingress.yaml
```

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods

# Check services
kubectl get svc

# Check ingress
kubectl get ingress

# Check logs
kubectl logs -f deployment/oauth-callback-server
kubectl logs -f deployment/mcp-server
```

### 7. Test

```bash
# Test OAuth callback service health
curl https://yourdomain.com/oauth/health

# Test MCP server (from client)
# Update simple_client.py with your domain:
# Client("https://yourdomain.com/mcp/")
python3 simple_client.py
```

## Architecture

### Local Development
```
┌────────────────────────────┐
│      main.py (port 8001)   │
│  ┌──────────────────────┐  │
│  │   MCP Server         │  │
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ OAuth Callback (8000)│  │
│  │  (built-in)          │  │
│  └──────────────────────┘  │
└────────────────────────────┘
```

### Kubernetes Production
```
                  ┌─────────────┐
                  │   Ingress   │
                  └──────┬──────┘
                         │
          ┌──────────────┴─────────────┐
          │                            │
    ┌─────▼─────┐              ┌───────▼────────┐
    │ OAuth     │              │  MCP Server    │
    │ Callback  │◄─────API─────┤  (Deployment)  │
    │ Service   │              │   Replicas: N  │
    │ :8000     │              │    :8001       │
    └───────────┘              └────────────────┘
```

## Environment Variables Reference

### MCP Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MICROSOFT_MCP_CLIENT_ID` | Yes | - | Azure AD Client ID |
| `MICROSOFT_MCP_CLIENT_SECRET` | Yes | - | Azure AD Client Secret |
| `MICROSOFT_MCP_TENANT_ID` | No | consumers | Azure AD Tenant ID |
| `MICROSOFT_MCP_REDIRECT_URI` | No | http://localhost:8000/callback | OAuth redirect URI |
| `MICROSOFT_MCP_ENABLE_CALLBACK_SERVER` | No | true | Enable built-in callback server |
| `MICROSOFT_MCP_OAUTH_CALLBACK_API_URL` | No | - | External callback API URL |
| `HOST` | No | 0.0.0.0 | Server bind address |
| `PORT` | No | 8001 | Server port |

### OAuth Callback Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OAUTH_CALLBACK_HOST` | No | 0.0.0.0 | Callback server bind address |
| `OAUTH_CALLBACK_PORT` | No | 8000 | Callback server port |

## Scaling

### OAuth Callback Server
- **Replicas: 1** (single instance due to in-memory storage)
- For high availability, replace in-memory storage with Redis

### MCP Server
- **Replicas: N** (can scale horizontally)
- Stateless, shares OAuth callback service

```bash
# Scale MCP server
kubectl scale deployment mcp-server --replicas=5
```

## Production Enhancements

### 1. Use Redis for Callback Storage

Replace in-memory dict in `oauth_callback_server.py` with Redis:

```python
import redis
r = redis.Redis(host='redis-service', port=6379, decode_responses=True)

# Store callback
r.setex(state, 600, json.dumps(callback_data))  # 10 min TTL

# Retrieve callback
data = r.get(state)
```

### 2. Add Monitoring

- Prometheus metrics
- Health check endpoints
- Logging to centralized system

### 3. Security

- Use TLS/HTTPS everywhere
- Rotate client secrets regularly
- Implement rate limiting
- Add authentication for MCP endpoints

## Troubleshooting

### Callback not received

```bash
# Check OAuth callback service logs
kubectl logs -f deployment/oauth-callback-server

# Check if service is accessible
kubectl port-forward svc/oauth-callback-service 8000:8000
curl http://localhost:8000/health
```

### MCP Server can't connect to callback service

```bash
# Test from within MCP pod
kubectl exec -it deployment/mcp-server -- curl http://oauth-callback-service:8000/health
```

### Ingress issues

```bash
# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Describe ingress
kubectl describe ingress mcp-ingress
```
