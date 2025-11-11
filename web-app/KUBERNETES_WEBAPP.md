# Deploying Web App to Kubernetes

## Architecture in Kubernetes

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                                                              │
│  ┌────────────┐      ┌─────────────┐      ┌──────────────┐ │
│  │            │      │             │      │              │ │
│  │  Ingress   │─────►│   Webapp    │─────►│  MCP Server  │ │
│  │  (NGINX)   │      │  (3 pods)   │      │  (N pods)    │ │
│  │            │      │             │      │              │ │
│  └────────────┘      └─────────────┘      └──────────────┘ │
│        │                    │                      │        │
│        │                    │                      │        │
│        ▼                    ▼                      ▼        │
│  ┌────────────┐      ┌─────────────┐      ┌──────────────┐ │
│  │  Callback  │      │    Redis    │      │   Callback   │ │
│  │  /oauth/*  │      │  (Sessions) │      │    Server    │ │
│  │            │      │             │      │   (1 pod)    │ │
│  └────────────┘      └─────────────┘      └──────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Changes for Kubernetes

### ✅ What Was Fixed:

1. **Service Discovery** - Uses Kubernetes service names instead of localhost
2. **Session Storage** - Redis for shared sessions across pods
3. **Configuration** - Environment variables for all settings
4. **Health Checks** - Kubernetes liveness/readiness probes
5. **Logging** - Proper app.logger usage
6. **Security** - Non-root user, secure cookies

## Prerequisites

1. **Kubernetes cluster** (GKE, EKS, AKS, or local minikube)
2. **kubectl** configured
3. **Docker registry** access
4. **cert-manager** (optional, for HTTPS)
5. **nginx-ingress** (optional, for Ingress)

## Step-by-Step Deployment

### 1. Build and Push Docker Images

```bash
# Build webapp image
cd microsoft-mcp
docker build -f Dockerfile.webapp -t your-registry/ms365-webapp:latest .
docker push your-registry/ms365-webapp:latest

# Build MCP server image (if not already done)
docker build -t your-registry/ms365-mcp-server:latest .
docker push your-registry/ms365-mcp-server:latest

# Build callback server image
cd ../callback-server
docker build -t your-registry/ms365-callback:latest .
docker push your-registry/ms365-callback:latest
```

### 2. Create Secrets

```bash
# Generate Flask secret key
kubectl create secret generic webapp-secrets \
  --from-literal=secret-key=$(openssl rand -hex 32)

# Azure AD credentials (if not already created)
kubectl create secret generic mcp-secrets \
  --from-literal=client-id=your-client-id \
  --from-literal=client-secret=your-client-secret
```

### 3. Deploy Services

```bash
# Deploy in order:

# 1. Redis (session storage)
kubectl apply -f kubernetes/webapp-deployment.yaml

# 2. Callback server
kubectl apply -f kubernetes/oauth-callback-deployment.yaml

# 3. MCP server
kubectl apply -f kubernetes/mcp-server-deployment.yaml

# 4. Web app
# (already included in webapp-deployment.yaml)
```

### 4. Configure Ingress (Optional but Recommended)

```bash
# Install nginx-ingress
helm install nginx-ingress ingress-nginx/ingress-nginx

# Install cert-manager for HTTPS
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
kubectl apply -f kubernetes/cluster-issuer.yaml

# Apply Ingress
kubectl apply -f kubernetes/webapp-deployment.yaml
```

### 5. Update Azure AD Redirect URI

In Azure Portal, update redirect URI to:
```
https://your-domain.com/oauth/callback
```

### 6. Verify Deployment

```bash
# Check all pods are running
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# View logs
kubectl logs -l app=webapp -f
kubectl logs -l app=mcp-server -f
kubectl logs -l app=oauth-callback -f
```

## Environment Variables

### Web App (webapp_k8s.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_URL` | `http://mcp-server-service:8001/mcp/` | MCP server endpoint |
| `REDIS_URL` | `redis://redis-service:6379` | Redis connection URL |
| `FLASK_SECRET_KEY` | (from secret) | Session encryption key |
| `SESSION_COOKIE_SECURE` | `true` | Require HTTPS for cookies |
| `FLASK_ENV` | `production` | Flask environment |
| `PORT` | `5000` | Port to listen on |

### MCP Server

| Variable | Value |
|----------|-------|
| `MICROSOFT_MCP_CLIENT_ID` | (from secret) |
| `MICROSOFT_MCP_CLIENT_SECRET` | (from secret) |
| `MICROSOFT_MCP_ENABLE_CALLBACK_SERVER` | `false` |
| `MICROSOFT_MCP_REDIRECT_URI` | `https://your-domain.com/oauth/callback` |
| `MICROSOFT_MCP_OAUTH_CALLBACK_API_URL` | `http://oauth-callback-service:8000/api/callback/{state}` |

## Scaling

```bash
# Scale webapp pods
kubectl scale deployment webapp --replicas=5

# Scale MCP server pods
kubectl scale deployment mcp-server --replicas=3

# Callback server should stay at 1 replica (in-memory storage)
# For multiple replicas, upgrade to Redis storage
```

## Monitoring

```bash
# Watch pod status
kubectl get pods -w

# Check resource usage
kubectl top pods

# View logs from all webapp pods
kubectl logs -l app=webapp --all-containers=true -f

# Check health endpoint
kubectl port-forward svc/webapp-service 8080:80
curl http://localhost:8080/health
```

## Troubleshooting

### Sessions Not Persisting

**Problem**: Users logged out after pod restart  
**Solution**: Check Redis connection
```bash
kubectl logs -l app=redis
kubectl exec -it <redis-pod> -- redis-cli ping
```

### Can't Connect to MCP Server

**Problem**: `connection refused` errors  
**Solution**: Verify service DNS
```bash
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
nslookup mcp-server-service
```

### OAuth Callback Not Working

**Problem**: Authentication hangs  
**Solution**: Check callback server and ingress routing
```bash
kubectl logs -l app=oauth-callback -f
kubectl describe ingress webapp-ingress
```

### High Memory Usage

**Problem**: Webapp pods using too much memory  
**Solution**: Reduce gunicorn workers or increase resource limits
```yaml
# In Dockerfile.webapp, change:
CMD ["gunicorn", "-w", "2", ...] # Reduce from 4 to 2 workers
```

## Production Checklist

- [ ] HTTPS enabled (cert-manager + Let's Encrypt)
- [ ] `SESSION_COOKIE_SECURE=true` set
- [ ] Secrets stored in Kubernetes Secrets (not in code)
- [ ] Resource limits configured
- [ ] Health checks working
- [ ] Horizontal Pod Autoscaling configured
- [ ] Redis persistence enabled (PersistentVolume)
- [ ] Monitoring/logging configured (Prometheus, Grafana)
- [ ] Backup strategy for Redis sessions
- [ ] Rate limiting configured (nginx-ingress)
- [ ] Network policies defined
- [ ] Azure AD redirect URI updated

## High Availability Setup

### Redis with Persistence

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
# Add to Redis deployment:
volumes:
- name: redis-storage
  persistentVolumeClaim:
    claimName: redis-pvc
volumeMounts:
- name: redis-storage
  mountPath: /data
```

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Costs Optimization

### Reduce Resources

```yaml
# For development/staging
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### Use Spot Instances

```bash
# On GKE
gcloud container node-pools create spot-pool \
  --cluster=my-cluster \
  --preemptible \
  --num-nodes=3
```

## Next Steps

1. Set up CI/CD pipeline (GitHub Actions, GitLab CI)
2. Configure monitoring (Prometheus + Grafana)
3. Set up log aggregation (ELK stack)
4. Implement rate limiting
5. Add caching layer (Redis for email data)
6. Implement WebSockets for real-time updates

## Support

For issues, check:
- Pod logs: `kubectl logs <pod-name>`
- Events: `kubectl get events --sort-by='.lastTimestamp'`
- Health checks: `curl http://<service-ip>/health`
