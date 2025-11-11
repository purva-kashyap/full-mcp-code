# Kubernetes Deployment Configuration

This directory contains Kubernetes manifests for deploying the Microsoft MCP Server.

## Architecture

```
┌─────────────────┐
│   Ingress       │ (yourdomain.com)
└────────┬────────┘
         │
    ┌────┴────┬──────────────┐
    │         │              │
    │         │              │
┌───▼────┐ ┌──▼───────┐ ┌───▼──────────┐
│  MCP   │ │  OAuth   │ │   Client     │
│ Server │ │ Callback │ │ Application  │
│:8001   │ │ Server   │ │              │
└────────┘ │  :8000   │ └──────────────┘
           └──────────┘
```

## Components

1. **OAuth Callback Service** (`oauth-callback-deployment.yaml`)
   - Handles OAuth redirects
   - Stores callback data temporarily
   - Exposes `/callback` endpoint

2. **MCP Server** (`mcp-server-deployment.yaml`)
   - Main MCP server
   - Connects to OAuth callback service via API
   - Exposes MCP tools on `/mcp/`

3. **Ingress** (`ingress.yaml`)
   - Routes traffic to both services
   - `/oauth/callback` → OAuth Callback Service
   - `/mcp/` → MCP Server

## Quick Start

1. **Create ConfigMap with credentials:**
```bash
kubectl create configmap mcp-config \
  --from-literal=MICROSOFT_MCP_CLIENT_ID=your-client-id \
  --from-literal=MICROSOFT_MCP_TENANT_ID=consumers
```

2. **Create Secret with client secret:**
```bash
kubectl create secret generic mcp-secret \
  --from-literal=MICROSOFT_MCP_CLIENT_SECRET=your-client-secret
```

3. **Deploy OAuth Callback Service:**
```bash
kubectl apply -f oauth-callback-deployment.yaml
kubectl apply -f oauth-callback-service.yaml
```

4. **Deploy MCP Server:**
```bash
kubectl apply -f mcp-server-deployment.yaml
kubectl apply -f mcp-server-service.yaml
```

5. **Deploy Ingress:**
```bash
kubectl apply -f ingress.yaml
```

## Configuration

### OAuth Callback Service
- Port: 8000
- Endpoints:
  - `/callback` - OAuth redirect endpoint
  - `/health` - Health check
  - `/api/callback/{state}` - API to retrieve callback data

### MCP Server
- Port: 8001
- Environment Variables:
  - `MICROSOFT_MCP_CLIENT_ID` - Azure AD Client ID
  - `MICROSOFT_MCP_CLIENT_SECRET` - Azure AD Client Secret
  - `MICROSOFT_MCP_TENANT_ID` - Azure AD Tenant ID or "consumers"
  - `MICROSOFT_MCP_REDIRECT_URI` - Full OAuth redirect URL (e.g., https://yourdomain.com/oauth/callback)
  - `MICROSOFT_MCP_OAUTH_CALLBACK_API_URL` - OAuth callback API URL (e.g., http://oauth-callback-service:8000/api/callback/{state})
  - `MICROSOFT_MCP_ENABLE_CALLBACK_SERVER` - Set to "false" in Kubernetes

## Scaling

The OAuth Callback Service should run as a single replica to maintain state consistency.
For production, replace the in-memory storage with Redis or a database.

The MCP Server can be scaled horizontally:
```bash
kubectl scale deployment mcp-server --replicas=3
```

## Monitoring

Check health:
```bash
# OAuth Callback Service
curl http://your-domain/oauth/health

# MCP Server (if health endpoint added)
curl http://your-domain/mcp/health
```

View logs:
```bash
kubectl logs -f deployment/oauth-callback-server
kubectl logs -f deployment/mcp-server
```
