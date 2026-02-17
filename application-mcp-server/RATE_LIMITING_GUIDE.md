# AsyncLimiter Implementation Guide

## 🎯 Overview

The application-mcp-server now includes **both concurrency control AND rate limiting** for precise API quota management.

## 🆕 What Changed

### Before:
- ✅ **Concurrency control** (Semaphore): Limit simultaneous requests
- ❌ **No rate limiting**: Could burst through quota quickly

### After:
- ✅ **Concurrency control** (Semaphore): Limit simultaneous requests  
- ✅ **Rate limiting** (AsyncLimiter): Match Microsoft Graph API quotas per endpoint

## 📊 How It Works

### Dual-Layer Protection

```
Request Flow:
┌─────────────────────────────────────────────┐
│ 1. Rate Limiter Check                       │
│    "Do I have quota available?"              │
│    Waits if quota exhausted                  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│ 2. Concurrency Slot Check                   │
│    "Is server capacity available?"           │
│    Waits if max concurrent reached           │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│ 3. Make API Request                         │
│    Execute the actual HTTP request           │
└─────────────────────────────────────────────┘
```

### Per-Endpoint Rate Limits

Different Microsoft Graph endpoints have different quotas:

| Endpoint Type | Rate Limit | Detection Pattern |
|--------------|------------|-------------------|
| **Mail** | 10,000 / 10 min | `/messages`, `/mailFolders` |
| **Calendar** | 10,000 / 10 min | `/calendar`, `/events` |
| **Teams Messages** | 120 / minute | `/channels/*/messages` |
| **Search** | 5 / second | `/search`, `$search` |
| **Users/Groups** | 10,000 / 10 min | `/users`, `/groups` |
| **Files** | 10,000 / 10 min | `/drive`, `/drives` |
| **Meetings** | 10,000 / 10 min | `/onlineMeetings` |
| **Global** | 2,000 / 10 sec | All other endpoints |

## 🔧 Implementation Details

### Files Created/Modified

1. **New: [rate_limiter.py](src/application_mcp/rate_limiter.py)**
   - AsyncLimiter management
   - Endpoint category detection
   - Per-endpoint limiter caching

2. **Updated: [graph.py](src/application_mcp/graph.py)**
   - Integrated rate limiting before concurrency check
   - Automatic endpoint categorization

3. **Updated: [config.py](src/application_mcp/config.py)**
   - Added rate limit configurations for all endpoint types
   - Configurable via environment variables

4. **Updated: [server.py](src/application_mcp/server.py)**
   - Added rate limiter stats to `/metrics` endpoint

5. **Updated: [requirements.txt](requirements.txt)**
   - Added `aiolimiter>=1.1.0`

## 📦 Installation

```bash
# Install the new dependency
pip install -r requirements.txt
```

## ⚙️ Configuration

### Environment Variables

Add to your `.env` file (see [.env.example](.env.example)):

```bash
# Global default
RATE_LIMIT_GLOBAL=2000,10          # 2000 req per 10 seconds

# Per-endpoint limits
RATE_LIMIT_MAIL=10000,600          # 10k per 10 minutes
RATE_LIMIT_CALENDAR=10000,600      # 10k per 10 minutes
RATE_LIMIT_TEAMS_MESSAGES=120,60   # 120 per minute
RATE_LIMIT_SEARCH=5,1              # 5 per second (very restrictive!)
RATE_LIMIT_USERS=10000,600         # 10k per 10 minutes
RATE_LIMIT_FILES=10000,600         # 10k per 10 minutes
RATE_LIMIT_MEETINGS=10000,600      # 10k per 10 minutes
```

### Format

```
RATE_LIMIT_<CATEGORY>=<max_requests>,<time_period_seconds>
```

Example:
- `RATE_LIMIT_SEARCH=5,1` = 5 requests per 1 second
- `RATE_LIMIT_MAIL=10000,600` = 10,000 requests per 600 seconds (10 minutes)

## 📈 Monitoring

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**New fields:**

```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "global": {
    "total_requests": 5000,
    "rate_limit_count": 2,
    "success_rate": 99.96
  },
  "endpoints": {
    "/users/{email}/messages": {
      "total_requests": 2500,
      "rate_limit_count": 0
    }
  },
  "rate_limiters": {
    "mail": {
      "max_rate": 10000,
      "time_period": 600,
      "current_level": 8234.5
    },
    "teams_messages": {
      "max_rate": 120,
      "time_period": 60,
      "current_level": 45.2
    }
  }
}
```

**Understanding rate_limiters:**
- `max_rate`: Maximum requests allowed
- `time_period`: Time window in seconds
- `current_level`: Current quota available (decreases with usage, refills over time)

### Logs

Rate limiters are initialized on first use:

```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "level": "INFO",
  "message": "Rate limiter initialized for 'mail' category",
  "category": "mail",
  "max_requests": 10000,
  "time_period_seconds": 600,
  "rate_per_second": 16.67
}
```

## 🎛️ Tuning Recommendations

### Conservative (Default)
Good for most deployments, stays well under limits:
```bash
RATE_LIMIT_GLOBAL=2000,10
RATE_LIMIT_MAIL=10000,600
```

### Aggressive
If you have premium API limits or need higher throughput:
```bash
RATE_LIMIT_GLOBAL=5000,10
RATE_LIMIT_MAIL=20000,600
```

### Teams-Heavy Workload
If you use Teams APIs extensively:
```bash
RATE_LIMIT_TEAMS_MESSAGES=100,60   # Slightly lower to be safe
```

### Search-Heavy Workload
Search is VERY restrictive:
```bash
RATE_LIMIT_SEARCH=4,1              # Even more conservative
```

## 🔬 Real-World Examples

### Example 1: Reading 5000 Emails

**Before (only concurrency control):**
```
- 50 concurrent requests at a time
- Each batch takes ~0.5s
- Total: ~50 seconds
- Risk: Could hit 10k/10min quota if done repeatedly
```

**After (with rate limiting):**
```
- Rate limiter: 10,000 per 10 minutes = ~16.67/sec
- Concurrency: 50 simultaneous max
- Requests smoothly distributed over time
- Total: ~50 seconds (similar speed)
- Benefit: Won't exhaust quota, predictable usage
```

### Example 2: Teams Channel Messages

**Before:**
```
- Get 500 messages from 10 channels
- Could fire 50 concurrent requests
- RESULT: 429 errors (Teams limit: 120/min)
```

**After:**
```
- Rate limiter: 120 per 60 seconds = 2/sec
- Requests automatically queued
- No 429 errors
- Takes longer but succeeds reliably
```

## 🚨 Troubleshooting

### "Requests seem slower"

**Cause:** Rate limiter is working! You're being throttled to match API limits.

**Check:**
```bash
curl http://localhost:8000/metrics
```

Look at `rate_limiters.current_level` - if it's near 0, you're at quota.

**Solutions:**
- Increase the rate limit if you have premium quotas
- Spread requests over longer time
- Check if you're using the right endpoint category

### "Still getting 429 errors"

**Possible causes:**

1. **Microsoft's limits are stricter** than documented
   - Solution: Lower your rate limits

2. **Other apps using same tenant quota**
   - Solution: Coordinate with other apps or lower limits

3. **Burst patterns**
   - Solution: Ensure rate limiter is enabled (check logs)

### "How do I know which limit I'm hitting?"

Check `/metrics` endpoint:

```json
"rate_limiters": {
  "mail": {
    "current_level": 0.5  // ⚠️ Almost at quota!
  }
}
```

If `current_level` is low, that category is throttling you.

## 🎯 Best Practices

1. **Start Conservative**
   - Use default rate limits
   - Monitor for 24-48 hours
   - Adjust based on actual usage

2. **Monitor Regularly**
   - Check `/metrics` daily
   - Set up alerts for `rate_limit_count > 0`
   - Watch `current_level` in limiters

3. **Tune Per-Endpoint**
   - If one endpoint is problematic, tune just that one
   - Don't globally increase if only one category needs it

4. **Combine with Concurrency**
   - Rate limiting controls quota usage
   - Concurrency controls server load
   - Both are needed for production

5. **Test Before Production**
   - Test with realistic load in staging
   - Verify no 429 errors
   - Ensure acceptable performance

## 📚 Further Reading

- **Microsoft Graph Throttling**: https://learn.microsoft.com/en-us/graph/throttling
- **AsyncLimiter Library**: https://github.com/mjpieters/aiolimiter
- **Rate Limiting Algorithms**: Token bucket vs Leaky bucket

## 🎉 Summary

You now have:
- ✅ **Concurrency control** (max simultaneous requests)
- ✅ **Rate limiting** (max requests per time period)
- ✅ **Per-endpoint limits** (match Microsoft's specific quotas)
- ✅ **Automatic categorization** (endpoints auto-detected)
- ✅ **Monitoring** (see quota usage in real-time)
- ✅ **Configurable** (tune for your needs)

This combination gives you **enterprise-grade quota management** for scaling to thousands of users! 🚀
