# Google Gemini API Configuration Guide

## 📋 Overview

This guide explains all Gemini-related environment variables used in TriageSync Backend for AI-powered triage functionality.

---

## 🔑 Required Fields

### 1. `GEMINI_API_KEY`

**Purpose:** Authentication key for Google Gemini API  
**Required:** ✅ Yes  
**Default:** None (must be provided)  
**Format:** String (API key from Google AI Studio)

```bash
GEMINI_API_KEY=AIzaSyDqBp3s2Flc7G1p9bEaXIIldX9TrDsHMDM
```

**How to Get:**
1. Visit https://ai.google.dev/
2. Sign in with Google account
3. Go to "Get API Key"
4. Create new API key or use existing one

**Important Notes:**
- ⚠️ **Never commit this to version control**
- ⚠️ **Keep it secret and secure**
- ⚠️ **Rotate regularly for security**
- ⚠️ **Monitor usage and quotas**

**Free Tier Limits:**
- **Per-minute:** 15 requests
- **Per-day:** 1,500 requests
- **Resets:** Midnight Pacific Time (PT)

**Paid Tier:** Visit https://ai.google.dev/pricing for higher limits

---

## 🎯 Model Selection & Fallback

### 2. `GEMINI_MODEL_PRIORITY`

**Purpose:** Defines which Gemini models to use and in what order  
**Required:** ❌ No (has default)  
**Default:** `gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b`  
**Format:** Comma-separated list of model names

```bash
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b
```

**How It Works:**
1. System tries models **left-to-right** in the order specified
2. If first model fails (quota/error), tries next model
3. Continues until a model succeeds or all fail
4. Each model has **independent quota**, so more models = more resilience

**Available Models:**
| Model | Speed | Quality | Free Tier Quota |
|-------|-------|---------|-----------------|
| `gemini-2.5-flash` | ⚡ Fastest | ⭐⭐⭐⭐ | 15/min, 1500/day |
| `gemini-2.5-flash-lite` | ⚡⚡ Very Fast | ⭐⭐⭐ | 15/min, 1500/day |
| `gemini-2.0-flash` | ⚡ Fast | ⭐⭐⭐⭐ | 15/min, 1500/day |
| `gemini-2.0-flash-lite` | ⚡⚡ Very Fast | ⭐⭐⭐ | 15/min, 1500/day |
| `gemini-1.5-flash` | ⚡ Fast | ⭐⭐⭐⭐ | 15/min, 1500/day |
| `gemini-1.5-flash-8b` | ⚡⚡⚡ Ultra Fast | ⭐⭐ | 15/min, 1500/day |

**Recommendations:**
- **Production:** Use all 6 models for maximum resilience
- **Development:** Use 2-3 models to save quota
- **Testing:** Use only `gemini-1.5-flash-8b` (fastest, lowest quality)

**Example Configurations:**

```bash
# Maximum resilience (recommended for production)
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b

# Balanced (good for staging)
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash

# Fast testing (development only)
GEMINI_MODEL_PRIORITY=gemini-1.5-flash-8b,gemini-2.0-flash-lite

# High quality only
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.0-flash
```

---

## ⚙️ API Call Configuration

### 3. `GEMINI_MAX_RETRIES`

**Purpose:** Number of retry attempts per model before moving to next model  
**Required:** ❌ No  
**Default:** `2`  
**Format:** Integer (1-10 recommended)

```bash
GEMINI_MAX_RETRIES=2
```

**How It Works:**
- If API call fails, retry up to this many times **for the same model**
- After max retries, moves to next model in priority list
- Total attempts per model = `GEMINI_MAX_RETRIES`

**Example Flow with `GEMINI_MAX_RETRIES=2`:**
```
1. Try gemini-2.5-flash (attempt 1) → Fail
2. Try gemini-2.5-flash (attempt 2) → Fail
3. Move to gemini-2.5-flash-lite (attempt 1) → Success ✅
```

**Recommendations:**
- **Production:** `2-3` (balance between resilience and speed)
- **Development:** `1-2` (faster feedback)
- **High-traffic:** `1` (fail fast, move to next model)

**Trade-offs:**
- ⬆️ Higher value = More resilient but slower
- ⬇️ Lower value = Faster but less resilient

---

### 4. `GEMINI_TIMEOUT_SECONDS`

**Purpose:** Maximum time to wait for API response per call  
**Required:** ❌ No  
**Default:** `8` seconds  
**Format:** Integer (seconds)

```bash
GEMINI_TIMEOUT_SECONDS=8
```

**How It Works:**
- If API call takes longer than this, it's cancelled
- Moves to retry or next model
- Prevents hanging requests

**Recommendations:**
- **Production:** `8-10` seconds (balance)
- **Fast response needed:** `5-6` seconds
- **Complex queries:** `10-15` seconds
- **Never exceed:** `30` seconds (user experience)

**Considerations:**
- Gemini API typically responds in 2-5 seconds
- Network latency adds 0.5-2 seconds
- Timeout should be: `expected_time + buffer`

**Example Scenarios:**
```bash
# Fast response (e-commerce, chatbots)
GEMINI_TIMEOUT_SECONDS=5

# Standard (most applications)
GEMINI_TIMEOUT_SECONDS=8

# Complex analysis (research, detailed reports)
GEMINI_TIMEOUT_SECONDS=15
```

---

### 5. `GEMINI_MODEL_LIST_TTL_SECONDS`

**Purpose:** Cache duration for available models list  
**Required:** ❌ No  
**Default:** `600` seconds (10 minutes)  
**Format:** Integer (seconds)

```bash
GEMINI_MODEL_LIST_TTL_SECONDS=600
```

**How It Works:**
- System calls `genai.list_models()` to check available models
- Result is cached for this duration
- Reduces API calls and improves performance

**Why This Matters:**
- `list_models()` is a network call to Google
- Without caching, every triage request would make this call
- Caching improves response time and reduces quota usage

**Recommendations:**
- **Production:** `600-3600` (10-60 minutes)
- **Development:** `300-600` (5-10 minutes)
- **Testing:** `60-300` (1-5 minutes)

**Trade-offs:**
- ⬆️ Higher value = Better performance, but slower to detect new models
- ⬇️ Lower value = More up-to-date, but more API calls

**Example Configurations:**
```bash
# High performance (production)
GEMINI_MODEL_LIST_TTL_SECONDS=3600  # 1 hour

# Balanced (default)
GEMINI_MODEL_LIST_TTL_SECONDS=600   # 10 minutes

# Frequent updates (development)
GEMINI_MODEL_LIST_TTL_SECONDS=300   # 5 minutes

# Testing new models
GEMINI_MODEL_LIST_TTL_SECONDS=60    # 1 minute
```

---

## 🔄 Circuit Breaker Configuration

The circuit breaker prevents wasting quota and time when the AI service is consistently failing.

### 6. `GEMINI_CIRCUIT_BREAKER_THRESHOLD`

**Purpose:** Number of consecutive failures before opening circuit  
**Required:** ❌ No  
**Default:** `5`  
**Format:** Integer (3-10 recommended)

```bash
GEMINI_CIRCUIT_BREAKER_THRESHOLD=5
```

**How It Works:**
1. Tracks consecutive failures across all models
2. After `N` consecutive failures, circuit "opens"
3. When open, AI calls are skipped (uses fallback)
4. Prevents wasting quota on failing service

**Example Flow:**
```
Request 1: All models fail → Failure count = 1
Request 2: All models fail → Failure count = 2
Request 3: All models fail → Failure count = 3
Request 4: All models fail → Failure count = 4
Request 5: All models fail → Failure count = 5
Circuit OPENS → Next requests use fallback (no AI calls)
... wait for cooldown ...
Circuit CLOSES → Try AI again
```

**Recommendations:**
- **Production:** `5-7` (balanced)
- **High availability:** `3-4` (fail fast)
- **Tolerant:** `8-10` (more attempts)

**Considerations:**
- Lower = Faster fallback, but may give up too soon
- Higher = More resilient, but wastes more quota

---

### 7. `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`

**Purpose:** How long circuit stays open before trying AI again  
**Required:** ❌ No  
**Default:** `30` seconds  
**Format:** Integer (seconds)

```bash
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30
```

**How It Works:**
1. When circuit opens, it stays open for this duration
2. During cooldown, all requests use fallback (no AI calls)
3. After cooldown, circuit closes and tries AI again
4. If AI succeeds, failure count resets to 0

**Recommendations:**
- **Production:** `30-60` seconds
- **Quick recovery:** `15-30` seconds
- **Conservative:** `60-120` seconds

**Example Scenarios:**
```bash
# Quick recovery (high-traffic sites)
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=15

# Standard (most applications)
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30

# Conservative (critical systems)
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=60

# Very conservative (low-traffic, high-reliability)
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=120
```

**Trade-offs:**
- ⬇️ Shorter = Faster recovery, but may retry too soon
- ⬆️ Longer = More stable, but longer fallback period

---

## 🎯 Configuration Presets

### Production (High Availability)
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b
GEMINI_MAX_RETRIES=2
GEMINI_TIMEOUT_SECONDS=8
GEMINI_MODEL_LIST_TTL_SECONDS=600
GEMINI_CIRCUIT_BREAKER_THRESHOLD=5
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30
```

### Production (Fast Response)
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash
GEMINI_MAX_RETRIES=1
GEMINI_TIMEOUT_SECONDS=5
GEMINI_MODEL_LIST_TTL_SECONDS=3600
GEMINI_CIRCUIT_BREAKER_THRESHOLD=3
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=15
```

### Development
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-1.5-flash
GEMINI_MAX_RETRIES=2
GEMINI_TIMEOUT_SECONDS=10
GEMINI_MODEL_LIST_TTL_SECONDS=300
GEMINI_CIRCUIT_BREAKER_THRESHOLD=5
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30
```

### Testing (Quota Conservation)
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL_PRIORITY=gemini-1.5-flash-8b
GEMINI_MAX_RETRIES=1
GEMINI_TIMEOUT_SECONDS=5
GEMINI_MODEL_LIST_TTL_SECONDS=60
GEMINI_CIRCUIT_BREAKER_THRESHOLD=3
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=15
```

---

## 📊 Monitoring & Troubleshooting

### Check Current Configuration

```python
# In Django shell
python manage.py shell

from django.conf import settings

print(f"API Key: {settings.GEMINI_API_KEY[:10]}...")
print(f"Model Priority: {settings.GEMINI_MODEL_PRIORITY}")
print(f"Max Retries: {settings.GEMINI_MAX_RETRIES}")
print(f"Timeout: {settings.GEMINI_TIMEOUT_SECONDS}s")
print(f"Cache TTL: {settings.GEMINI_MODEL_LIST_TTL_SECONDS}s")
print(f"Circuit Threshold: {settings.GEMINI_CIRCUIT_BREAKER_THRESHOLD}")
print(f"Circuit Cooldown: {settings.GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS}s")
```

### Common Issues

#### 1. 503 Service Unavailable
**Cause:** Quota exceeded or circuit breaker open  
**Solution:**
- Wait for quota reset (midnight PT)
- Check circuit breaker status
- Upgrade to paid tier

#### 2. Slow Response Times
**Cause:** High timeout or too many retries  
**Solution:**
- Reduce `GEMINI_TIMEOUT_SECONDS`
- Reduce `GEMINI_MAX_RETRIES`
- Use faster models (flash-lite, flash-8b)

#### 3. Frequent Fallback Usage
**Cause:** Circuit breaker opening too often  
**Solution:**
- Increase `GEMINI_CIRCUIT_BREAKER_THRESHOLD`
- Increase `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`
- Check API key validity
- Verify quota limits

#### 4. Model Not Found Errors
**Cause:** Model not available for your API key  
**Solution:**
- Check available models at https://ai.google.dev/models
- Update `GEMINI_MODEL_PRIORITY` with available models
- Reduce `GEMINI_MODEL_LIST_TTL_SECONDS` to refresh cache

---

## 🔒 Security Best Practices

1. **Never commit API key to version control**
   ```bash
   # .gitignore should include:
   .env
   .env.*
   ```

2. **Rotate API keys regularly**
   - Monthly for production
   - After any suspected compromise

3. **Use environment-specific keys**
   - Development key for local testing
   - Staging key for staging environment
   - Production key for production only

4. **Monitor API usage**
   - Set up alerts for quota limits
   - Track usage patterns
   - Review logs regularly

5. **Restrict API key permissions**
   - Use Google Cloud IAM for fine-grained control
   - Limit to specific services
   - Set IP restrictions if possible

---

## 📈 Performance Optimization

### For High Traffic
```bash
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.0-flash  # Fewer models
GEMINI_MAX_RETRIES=1                                      # Fail fast
GEMINI_TIMEOUT_SECONDS=5                                  # Quick timeout
GEMINI_MODEL_LIST_TTL_SECONDS=3600                       # Long cache
GEMINI_CIRCUIT_BREAKER_THRESHOLD=3                       # Quick fallback
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=15               # Quick recovery
```

### For High Reliability
```bash
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b
GEMINI_MAX_RETRIES=3                                      # More retries
GEMINI_TIMEOUT_SECONDS=10                                 # Generous timeout
GEMINI_MODEL_LIST_TTL_SECONDS=600                        # Standard cache
GEMINI_CIRCUIT_BREAKER_THRESHOLD=7                       # Tolerant
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=60               # Conservative
```

---

## ✅ Verification Checklist

- [ ] `GEMINI_API_KEY` is set and valid
- [ ] `GEMINI_MODEL_PRIORITY` includes at least 2 models
- [ ] `GEMINI_MAX_RETRIES` is between 1-3
- [ ] `GEMINI_TIMEOUT_SECONDS` is between 5-15
- [ ] `GEMINI_MODEL_LIST_TTL_SECONDS` is between 300-3600
- [ ] `GEMINI_CIRCUIT_BREAKER_THRESHOLD` is between 3-10
- [ ] `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS` is between 15-120
- [ ] API key is not committed to version control
- [ ] Quota limits are understood and monitored

---

**Last Updated:** May 1, 2026  
**Version:** 1.0
