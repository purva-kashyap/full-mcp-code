# OAuth Callback Server

A standalone OAuth callback service for Microsoft MCP Server.

## Purpose

This service handles OAuth redirects from Microsoft and stores callback data temporarily, allowing the MCP server to retrieve it via API. Designed for Kubernetes deployments where the callback server runs separately from the MCP server.

## Features

- ✅ Handles OAuth callbacks from Microsoft
- ✅ Stores callback data with auto-expiry (10 minutes)
- ✅ Provides API for retrieving callbacks
- ✅ Health check endpoint for Kubernetes
- ✅ Zero dependencies (uses Python stdlib only)
- ✅ CORS enabled for cross-origin requests

## Quick Start

### Local Testing

```bash
python3 oauth_callback_server.py
```

Server starts on `http://0.0.0.0:8000`

### Docker

```bash
# Build
docker build -t oauth-callback-server .

# Run
docker run -p 8000:8000 oauth-callback-server
```

### Kubernetes

```bash
kubectl apply -f deployment.yaml
```

## Endpoints

### 1. OAuth Callback
- **URL**: `/callback`
- **Method**: GET
- **Purpose**: Receives OAuth redirect from Microsoft
- **Parameters**: 
  - `code` - Authorization code
  - `state` - CSRF protection state
  - `error` - Error code (if any)

### 2. Health Check
- **URL**: `/health`
- **Method**: GET
- **Response**: 
```json
{
  "status": "healthy",
  "service": "oauth-callback-server",
  "timestamp": "2025-11-10T12:00:00",
  "active_callbacks": 5
}
```

### 3. Retrieve Callback
- **URL**: `/api/callback/{state}`
- **Method**: GET
- **Response**: 
```json
{
  "status": "success",
  "auth_code": "xxx",
  "state": "yyy",
  "error": null,
  "error_description": null
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OAUTH_CALLBACK_HOST` | `0.0.0.0` | Host to bind to |
| `OAUTH_CALLBACK_PORT` | `8000` | Port to listen on |

### Azure AD Setup

Configure your Azure AD app redirect URI to point to:
- **Local**: `http://localhost:8000/callback`
- **Production**: `https://yourdomain.com/oauth/callback`

## How It Works

```
1. User clicks auth link
   ↓
2. Microsoft redirects to /callback?code=xxx&state=yyy
   ↓
3. Server stores callback data in memory
   ↓
4. MCP Server polls /api/callback/{state}
   ↓
5. Server returns callback data (one-time retrieval)
   ↓
6. Data auto-expires after 10 minutes
```

## Production Deployment

### Single Instance
The default implementation uses in-memory storage, so run only 1 replica:

```yaml
spec:
  replicas: 1
```

### High Availability with Redis

For HA, replace in-memory storage with Redis:

```python
import redis
r = redis.Redis(host='redis-service', port=6379)

# Store
r.setex(state, 600, json.dumps(callback_data))

# Retrieve
data = r.get(state)
```

Then scale to multiple replicas:
```bash
kubectl scale deployment oauth-callback-server --replicas=3
```

## Security Considerations

- ✅ Auto-expiry prevents stale data accumulation
- ✅ One-time retrieval prevents replay attacks
- ✅ State parameter validation
- ✅ CORS headers for controlled access
- ⚠️ HTTPS required in production
- ⚠️ Consider rate limiting for production

## Monitoring

### Logs
```bash
# Docker
docker logs -f oauth-callback-server

# Kubernetes
kubectl logs -f deployment/oauth-callback-server
```

### Metrics
Check health endpoint:
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Port already in use
```bash
# Find process
lsof -ti:8000

# Kill it
lsof -ti:8000 | xargs kill -9
```

### Callback not received
1. Check Azure AD redirect URI matches exactly
2. Verify server is accessible from browser
3. Check firewall/network settings
4. Review server logs

### API returns 404
- Callback hasn't been received yet
- State parameter is incorrect
- Callback expired (>10 minutes old)
- Callback already retrieved

## Development

### Run with Debug Logging
```python
# Uncomment log_message method in oauth_callback_server.py
def log_message(self, format, *args):
    print(f"[{datetime.now().isoformat()}] {format % args}", file=sys.stderr)
```

### Test Locally
```bash
# Terminal 1: Start callback server
python3 oauth_callback_server.py

# Terminal 2: Test health
curl http://localhost:8000/health

# Terminal 3: Simulate callback
curl "http://localhost:8000/callback?code=test123&state=abc456"

# Terminal 4: Retrieve callback
curl http://localhost:8000/api/callback/abc456
```

## Architecture

```
┌──────────────┐
│   Browser    │
└──────┬───────┘
       │ OAuth redirect
       ↓
┌──────────────────┐
│ /callback        │
│                  │
│ Callback Server  │◄──── API poll ────┐
│ :8000            │                    │
│                  │                    │
│ /api/callback/   │                    │
│ /health          │                    │
└──────────────────┘                    │
                                   ┌────┴────┐
                                   │   MCP   │
                                   │  Server │
                                   └─────────┘
```

## License

MIT
