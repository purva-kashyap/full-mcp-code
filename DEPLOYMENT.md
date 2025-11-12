# Kubernetes Deployment Guide

Complete guide for deploying MCP Server and MCP Web App to Kubernetes.

## 📋 Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Docker installed
- NGINX Ingress Controller (optional, for Ingress)
- cert-manager (optional, for TLS)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  Kubernetes Cluster (mcp-system namespace)          │
│                                                      │
│  ┌────────────────────┐    ┌──────────────────────┐│
│  │  MCP Web App       │    │  MCP Server          ││
│  │  (2 replicas)      │◄───┤  (1 replica)         ││
│  │  Port: 5001        │    │  Ports: 8000, 8001   ││
│  └────────────────────┘    └──────────────────────┘│
│           │                          │              │
│           │                          │              │
│  ┌────────▼──────────────────────────▼────────────┐│
│  │         Ingress Controller (NGINX)             ││
│  └────────────────────────────────────────────────┘│
└──────────────────────┬──────────────────────────────┘
                       │
                ┌──────▼────────┐
                │   Internet    │
                └───────────────┘
```

## 🚀 Quick Start

### 1. Update Configuration

#### MCP Server Secrets (`mcp-server/k8s/secret.yaml`):
```bash
# Replace with your Azure AD credentials
AZURE_CLIENT_ID: "your-client-id"
AZURE_CLIENT_SECRET: "your-client-secret"
AZURE_TENANT_ID: "consumers"
```

#### Update Domains:
- `mcp-server/k8s/ingress.yaml` → Update `host` with your domain
- `mcp-server/k8s/configmap.yaml` → Update `OAUTH_REDIRECT_URI`
- `mcp-web-app/k8s/ingress.yaml` → Update `host` with your domain
- `mcp-web-app/k8s/configmap.yaml` → Update `CALLBACK_BASE_URL`

### 2. Build Docker Images

```bash
# MCP Server
cd mcp-server
docker build -t your-registry/mcp-server:latest .
docker push your-registry/mcp-server:latest

# MCP Web App
cd ../mcp-web-app
docker build -t your-registry/mcp-web-app:latest .
docker push your-registry/mcp-web-app:latest
```

### 3. Deploy to Kubernetes

#### Option A: Using deploy script (recommended)
```bash
./deploy.sh
```

#### Option B: Manual deployment
```bash
# Create namespace
kubectl apply -f mcp-server/k8s/namespace.yaml

# Deploy MCP Server
kubectl apply -f mcp-server/k8s/secret.yaml
kubectl apply -f mcp-server/k8s/configmap.yaml
kubectl apply -f mcp-server/k8s/pvc.yaml
kubectl apply -f mcp-server/k8s/deployment.yaml
kubectl apply -f mcp-server/k8s/ingress.yaml

# Deploy MCP Web App
kubectl apply -f mcp-web-app/k8s/configmap.yaml
kubectl apply -f mcp-web-app/k8s/deployment.yaml
kubectl apply -f mcp-web-app/k8s/ingress.yaml
```

## 📦 Components

### MCP Server
- **Deployment**: 1 replica (due to in-memory callback storage)
- **Service**: ClusterIP with session affinity
- **Ports**: 8000 (FastAPI), 8001 (MCP)
- **PVC**: 1Gi for token cache
- **Health Check**: `/health` endpoint

### MCP Web App
- **Deployment**: 2 replicas (stateless, can scale)
- **Service**: ClusterIP
- **Port**: 5001 (mapped to 80 in service)
- **Health Check**: `/` endpoint

## ⚙️ Configuration

### Environment Variables

**MCP Server:**
- `AZURE_CLIENT_ID` - Azure AD application ID
- `AZURE_CLIENT_SECRET` - Azure AD client secret
- `AZURE_TENANT_ID` - Azure AD tenant (default: "consumers")
- `OAUTH_REDIRECT_URI` - OAuth callback URL

**MCP Web App:**
- `SECRET_KEY` - Flask session secret
- `MCP_SERVER_URL` - MCP server endpoint (default: `http://mcp-server:8001/mcp`)
- `CALLBACK_BASE_URL` - OAuth callback base URL

### Storage

**Token Cache:**
- PersistentVolumeClaim: `mcp-token-cache`
- Size: 1Gi
- AccessMode: ReadWriteOnce
- Mounted at: `/root` (contains `~/.hybrid_mcp_token_cache.json`)

## 🔍 Monitoring

### Check Status
```bash
# Get all resources
kubectl get all -n mcp-system

# Check pods
kubectl get pods -n mcp-system

# Check services
kubectl get svc -n mcp-system

# Check ingress
kubectl get ingress -n mcp-system
```

### View Logs
```bash
# MCP Server
kubectl logs -f deployment/mcp-server -n mcp-system

# MCP Web App
kubectl logs -f deployment/mcp-web-app -n mcp-system

# Specific pod
kubectl logs -f <pod-name> -n mcp-system
```

### Debug
```bash
# Describe resources
kubectl describe pod <pod-name> -n mcp-system
kubectl describe deployment mcp-server -n mcp-system

# Get events
kubectl get events -n mcp-system --sort-by='.lastTimestamp'

# Access pod shell
kubectl exec -it <pod-name> -n mcp-system -- /bin/bash
```

## 🔒 Security Considerations

1. **Secrets Management**: Use Kubernetes Secrets or external secret managers (Vault, AWS Secrets Manager)
2. **TLS**: Enable TLS in Ingress with cert-manager
3. **Network Policies**: Restrict pod-to-pod communication
4. **RBAC**: Configure service accounts with minimal permissions
5. **Image Security**: Scan images for vulnerabilities

## 📈 Scaling

### MCP Web App (Stateless)
```bash
# Scale horizontally
kubectl scale deployment mcp-web-app --replicas=5 -n mcp-system
```

### MCP Server (Stateful - Limited)
⚠️ **Important**: MCP Server uses in-memory callback storage
- **Current**: 1 replica with session affinity
- **For multiple replicas**: Implement Redis-backed callback storage

## 🔄 Updates

### Rolling Update
```bash
# Update image
kubectl set image deployment/mcp-server mcp-server=your-registry/mcp-server:v2 -n mcp-system

# Check rollout status
kubectl rollout status deployment/mcp-server -n mcp-system

# Rollback if needed
kubectl rollout undo deployment/mcp-server -n mcp-system
```

## 🧹 Cleanup

```bash
# Delete all resources
kubectl delete namespace mcp-system

# Or delete individually
kubectl delete -f mcp-server/k8s/
kubectl delete -f mcp-web-app/k8s/
```

## 🐛 Troubleshooting

### Pod not starting
```bash
kubectl describe pod <pod-name> -n mcp-system
kubectl logs <pod-name> -n mcp-system
```

### Service not accessible
```bash
# Test from another pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n mcp-system -- sh
curl http://mcp-server:8000/health
```

### Ingress not working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress
kubectl describe ingress -n mcp-system
```

## 📝 Production Checklist

- [ ] Update all placeholder domains in Ingress
- [ ] Configure proper Azure AD redirect URIs
- [ ] Set strong SECRET_KEY for Flask
- [ ] Enable TLS with cert-manager
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure log aggregation (ELK, Loki)
- [ ] Set resource limits appropriately
- [ ] Configure autoscaling (HPA) for web app
- [ ] Implement Redis for MCP Server callback storage
- [ ] Set up backup for PVC (token cache)
- [ ] Configure network policies
- [ ] Enable pod security policies

## 🔗 Related Documentation

- [MCP Server Architecture](../mcp-server/ARCHITECTURE.md)
- [Web App README](../mcp-web-app/README.md)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
