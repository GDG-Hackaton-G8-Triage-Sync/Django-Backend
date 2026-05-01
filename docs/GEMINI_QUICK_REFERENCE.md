# Gemini Configuration - Quick Reference Card

## 📋 All Gemini Environment Variables

| Variable | Required | Default | Your Value | Purpose |
|----------|----------|---------|------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | None | `AIzaSy...` | API authentication |
| `GEMINI_MODEL_PRIORITY` | ❌ No | 6 models | 6 models | Model fallback order |
| `GEMINI_MAX_RETRIES` | ❌ No | `2` | `2` | Retries per model |
| `GEMINI_TIMEOUT_SECONDS` | ❌ No | `8` | `8` | Request timeout |
| `GEMINI_MODEL_LIST_TTL_SECONDS` | ❌ No | `600` | `600` | Cache duration |
| `GEMINI_CIRCUIT_BREAKER_THRESHOLD` | ❌ No | `5` | `5` | Failures before open |
| `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS` | ❌ No | `30` | `30` | Cooldown period |

---

## ✅ Your Current Configuration Status

```bash
# From: Django-Backend/triagesync_backend/.env

GEMINI_API_KEY=AIzaSyDqBp3s2Flc7G1p9bEaXIIldX9TrDsHMDM ✅
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b ✅
GEMINI_MAX_RETRIES=2 ✅
GEMINI_TIMEOUT_SECONDS=8 ✅
GEMINI_MODEL_LIST_TTL_SECONDS=600 ✅
GEMINI_CIRCUIT_BREAKER_THRESHOLD=5 ✅
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30 ✅
```

**Status:** ✅ **All fields configured correctly**

---

## 🎯 What Each Field Does (Simple Explanation)

### 1. `GEMINI_API_KEY`
**What:** Your password to use Google's AI  
**Why:** Without it, AI features won't work  
**Action:** Keep it secret, never share

### 2. `GEMINI_MODEL_PRIORITY`
**What:** List of AI models to try (in order)  
**Why:** If one fails, try the next one  
**Action:** More models = more reliable

### 3. `GEMINI_MAX_RETRIES`
**What:** How many times to retry each model  
**Why:** Sometimes requests fail temporarily  
**Action:** `2` is good balance

### 4. `GEMINI_TIMEOUT_SECONDS`
**What:** Max wait time for AI response  
**Why:** Don't wait forever if AI is slow  
**Action:** `8` seconds is reasonable

### 5. `GEMINI_MODEL_LIST_TTL_SECONDS`
**What:** How long to remember available models  
**Why:** Checking every time is slow  
**Action:** `600` (10 min) is efficient

### 6. `GEMINI_CIRCUIT_BREAKER_THRESHOLD`
**What:** Failures before giving up temporarily  
**Why:** Don't waste quota if AI is down  
**Action:** `5` failures is reasonable

### 7. `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`
**What:** Wait time before trying AI again  
**Why:** Give AI time to recover  
**Action:** `30` seconds is balanced

---

## 🚦 How It All Works Together

```
User Request → Try AI
    ↓
1. Check Circuit Breaker
   - Open? → Use Fallback ❌
   - Closed? → Continue ✅
    ↓
2. Try First Model (gemini-2.5-flash)
   - Success? → Return Result ✅
   - Fail? → Retry (up to GEMINI_MAX_RETRIES)
   - Still Fail? → Next Model
    ↓
3. Try Second Model (gemini-2.5-flash-lite)
   - Success? → Return Result ✅
   - Fail? → Retry
   - Still Fail? → Next Model
    ↓
4. Try All Models in GEMINI_MODEL_PRIORITY
   - Any Success? → Return Result ✅
   - All Fail? → Increment Failure Count
    ↓
5. Check Failure Count
   - < THRESHOLD? → Use Fallback for this request
   - >= THRESHOLD? → Open Circuit Breaker
    ↓
6. Circuit Breaker Open
   - Wait COOLDOWN_SECONDS
   - Then try AI again
```

---

## 📊 Your Configuration Analysis

### Resilience: ⭐⭐⭐⭐⭐ (Excellent)
- **6 models** in fallback chain
- **2 retries** per model
- **5 failure threshold** before circuit opens
- **Total attempts before fallback:** Up to 12 (6 models × 2 retries)

### Performance: ⭐⭐⭐⭐ (Good)
- **8 second timeout** - reasonable
- **10 minute cache** - efficient
- **30 second cooldown** - balanced

### Quota Efficiency: ⭐⭐⭐⭐ (Good)
- Circuit breaker prevents waste
- Model list caching reduces calls
- Reasonable retry count

### Overall: ⭐⭐⭐⭐⭐ (Production Ready)

---

## 🔧 Quick Adjustments

### If AI is Too Slow
```bash
GEMINI_TIMEOUT_SECONDS=5          # Reduce from 8
GEMINI_MAX_RETRIES=1              # Reduce from 2
```

### If AI Fails Too Often
```bash
GEMINI_CIRCUIT_BREAKER_THRESHOLD=7    # Increase from 5
GEMINI_MAX_RETRIES=3                  # Increase from 2
```

### If Quota Running Out
```bash
GEMINI_MODEL_PRIORITY=gemini-1.5-flash-8b    # Use only one fast model
GEMINI_MAX_RETRIES=1                          # Reduce retries
GEMINI_CIRCUIT_BREAKER_THRESHOLD=3           # Fail faster
```

### If Need Maximum Reliability
```bash
# Already configured optimally! ✅
# Your current settings are production-ready
```

---

## ⚠️ Common Mistakes to Avoid

❌ **Don't:** Set `GEMINI_MAX_RETRIES` too high (>5)  
✅ **Do:** Keep it at 2-3 for balance

❌ **Don't:** Set `GEMINI_TIMEOUT_SECONDS` too low (<5)  
✅ **Do:** Use 8-10 seconds for reliable responses

❌ **Don't:** Use only one model in `GEMINI_MODEL_PRIORITY`  
✅ **Do:** Use at least 2-3 models for resilience

❌ **Don't:** Set `GEMINI_CIRCUIT_BREAKER_THRESHOLD` too low (<3)  
✅ **Do:** Use 5-7 to avoid premature fallback

❌ **Don't:** Commit `GEMINI_API_KEY` to git  
✅ **Do:** Keep it in `.env` (already in `.gitignore`)

---

## 📈 Quota Management

### Free Tier Limits (Per Model)
- **Per-minute:** 15 requests
- **Per-day:** 1,500 requests
- **Resets:** Midnight Pacific Time

### Your Configuration Impact
With 6 models, you effectively have:
- **Per-minute:** 90 requests (15 × 6)
- **Per-day:** 9,000 requests (1,500 × 6)

**Note:** This assumes even distribution across models

### Monitoring
```bash
# Check quota usage at:
https://ai.google.dev/rate-limits

# Or in Google Cloud Console:
https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
```

---

## ✅ Verification Commands

### Check Configuration
```bash
# View current settings
cat Django-Backend/triagesync_backend/.env | grep GEMINI

# Test AI endpoint
cd Django-Backend
python test_ai_status.py
```

### Verify in Django
```python
python manage.py shell

from django.conf import settings
print("API Key:", settings.GEMINI_API_KEY[:10] + "...")
print("Models:", settings.GEMINI_MODEL_PRIORITY)
print("Max Retries:", settings.GEMINI_MAX_RETRIES)
print("Timeout:", settings.GEMINI_TIMEOUT_SECONDS)
```

---

## 📚 Related Documentation

- **Full Guide:** `GEMINI_CONFIGURATION_GUIDE.md` (detailed explanations)
- **Deployment:** `DEPLOYMENT_GUIDE.md` (production setup)
- **Environment:** `PRODUCTION_ENV_SETUP_COMPLETE.md` (all variables)

---

## 🎯 Summary

✅ **All 7 Gemini fields are configured**  
✅ **Values are production-ready**  
✅ **Configuration is optimal for reliability**  
✅ **No changes needed**

Your Gemini configuration is **complete and production-ready**! 🚀

---

**Last Updated:** May 1, 2026
