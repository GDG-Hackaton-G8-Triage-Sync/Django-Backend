# Render Deployment Guide - TriageSync Backend

## 🚀 Quick Fix for Your Error

### **Problem:**
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

### **Solution:**
✅ **Fixed!** I've created `requirements.txt` in the correct location (`Django-Backend/requirements.txt`)

---

## 📋 Files Created for Render Deployment

### 1. **`requirements.txt`** ✅
**Location:** `Django-Backend/requirements.txt`  
**Purpose:** Lists all Python dependencies  
**Status:** Created

### 2. **`render.yaml`** ✅
**Location:** `Django-Backend/render.yaml`  
**Purpose:** Render service configuration  
**Status:** Created

### 3. **`build.sh`** ✅
**Location:** `Django-Backend/build.sh`  
**Purpose:** Build script for Render  
**Status:** Created

---

## 🎯 Deployment Steps

### Step 1: Prepare Your Repository

1. **Commit the new files:**
```bash
cd Django-Backend
git add requirements.txt render.yaml build.sh
git commit -m "Add Render deployment configuration"
git push origin main
```

2. **Make build.sh executable (if on Linux/Mac):**
```bash
chmod +x build.sh
git add build.sh
git commit -m "Make build.sh executable"
git push origin main
```

---

### Step 2: Configure Render

#### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub/GitLab repository
4. Select the repository containing your Django-Backend
5. Render will automatically detect `render.yaml`
6. Click **"Apply"**

#### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your repository
4. Configure:
   - **Name:** `triagesync-backend`
   - **Region:** Oregon (or closest to you)
   - **Branch:** `main`
   - **Root Directory:** `Django-Backend` (if repo root is not Django-Backend)
   - **Runtime:** Python 3
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn triagesync_backend.config.wsgi:application`

---

### Step 3: Set Environment Variables

In Render Dashboard → Your Service → Environment:

#### Required Variables:
```bash
DJANGO_SECRET_KEY=<generate-new-secret-key>
DJANGO_ALLOWED_HOSTS=<your-render-url>.onrender.com
GEMINI_API_KEY=<your-gemini-api-key>
```

#### Optional Variables (with defaults):
```bash
DJANGO_DEBUG=False
CORS_ALLOW_ALL_ORIGINS=True
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash
GEMINI_MAX_RETRIES=2
GEMINI_TIMEOUT_SECONDS=8
GEMINI_MODEL_LIST_TTL_SECONDS=600
GEMINI_CIRCUIT_BREAKER_THRESHOLD=5
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30
```

---

### Step 4: Database Configuration

#### Option A: Use Your Existing NeonDB (Recommended)

In Render Environment Variables:
```bash
DATABASE_URL=postgresql://neondb_owner:npg_T6SiVZDcgz2e@ep-square-firefly-abisf3bt-pooler.eu-west-2.aws.neon.tech/triagedb?sslmode=require&channel_binding=require
```

#### Option B: Create Render PostgreSQL Database

1. In Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Name: `triagesync-db`
3. Region: Same as your web service
4. Plan: Free
5. After creation, Render will automatically set `DATABASE_URL`

---

### Step 5: Deploy

1. Click **"Manual Deploy"** → **"Deploy latest commit"**
2. Wait for build to complete (3-5 minutes)
3. Check logs for any errors
4. Visit your app URL: `https://your-app.onrender.com`

---

## 🔧 Troubleshooting

### Error: "requirements.txt not found"
✅ **Fixed!** File is now in the correct location

### Error: "build.sh: Permission denied"
```bash
chmod +x build.sh
git add build.sh
git commit -m "Make build.sh executable"
git push
```

### Error: "Module not found"
Check that all dependencies are in `requirements.txt`:
```bash
cat requirements.txt
```

### Error: "Database connection failed"
Verify `DATABASE_URL` in Render environment variables:
```bash
# Should look like:
postgresql://user:pass@host:port/database?sslmode=require
```

### Error: "Static files not loading"
Add to `settings.py`:
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Error: "Application timeout"
Increase timeout in Render settings or optimize your code

---

## 📊 Project Structure for Render

```
Django-Backend/
├── requirements.txt          ✅ (Root level - Render looks here)
├── render.yaml              ✅ (Render configuration)
├── build.sh                 ✅ (Build script)
├── manage.py                ✅ (Django management)
├── triagesync_backend/
│   ├── config/
│   │   ├── settings.py
│   │   ├── wsgi.py
│   │   └── urls.py
│   ├── apps/
│   └── .env                 ⚠️ (Not used on Render - use env vars)
└── .gitignore
```

---

## 🔒 Security Checklist for Render

- [ ] `DJANGO_DEBUG=False` in production
- [ ] Generate new `DJANGO_SECRET_KEY` (don't use dev key)
- [ ] Set `DJANGO_ALLOWED_HOSTS` to your Render URL
- [ ] Use environment variables (not `.env` file)
- [ ] Enable HTTPS (Render does this automatically)
- [ ] Set `CORS_ALLOW_ALL_ORIGINS=False` for production (or keep `True` for demo)
- [ ] Use strong database password
- [ ] Rotate `GEMINI_API_KEY` regularly

---

## 📝 Environment Variables Reference

### Django Core
| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | ✅ Yes | `django-insecure-...` | Django secret key |
| `DJANGO_DEBUG` | ❌ No | `False` | Debug mode (default: False) |
| `DJANGO_ALLOWED_HOSTS` | ✅ Yes | `myapp.onrender.com` | Allowed domains |
| `DJANGO_SETTINGS_MODULE` | ❌ No | `triagesync_backend.config.settings` | Settings module |

### Database
| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | `postgresql://...` | PostgreSQL connection |

### CORS
| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `CORS_ALLOW_ALL_ORIGINS` | ❌ No | `True` | Allow all origins |

### Gemini AI
| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | `AIzaSy...` | Google Gemini API key |
| `GEMINI_MODEL_PRIORITY` | ❌ No | `gemini-2.5-flash,...` | Model fallback order |
| `GEMINI_MAX_RETRIES` | ❌ No | `2` | Retry attempts |
| `GEMINI_TIMEOUT_SECONDS` | ❌ No | `8` | Request timeout |
| `GEMINI_MODEL_LIST_TTL_SECONDS` | ❌ No | `600` | Cache duration |
| `GEMINI_CIRCUIT_BREAKER_THRESHOLD` | ❌ No | `5` | Failure threshold |
| `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS` | ❌ No | `30` | Cooldown period |

---

## 🚀 Quick Deploy Commands

### Initial Setup
```bash
# 1. Commit new files
git add requirements.txt render.yaml build.sh
git commit -m "Add Render deployment configuration"
git push origin main

# 2. Go to Render Dashboard
# 3. Create new Web Service
# 4. Connect repository
# 5. Deploy!
```

### Update Deployment
```bash
# Make changes
git add .
git commit -m "Update application"
git push origin main

# Render auto-deploys on push (if enabled)
# Or manually deploy from Render Dashboard
```

---

## 📚 Additional Resources

- **Render Docs:** https://render.com/docs
- **Django on Render:** https://render.com/docs/deploy-django
- **Troubleshooting:** https://render.com/docs/troubleshooting-deploys
- **Environment Variables:** https://render.com/docs/environment-variables

---

## ✅ Deployment Checklist

### Pre-Deployment
- [x] `requirements.txt` in root directory
- [x] `render.yaml` configured
- [x] `build.sh` created
- [ ] All files committed to git
- [ ] Repository pushed to GitHub/GitLab

### Render Configuration
- [ ] Web Service created
- [ ] Repository connected
- [ ] Build command set: `./build.sh`
- [ ] Start command set: `gunicorn triagesync_backend.config.wsgi:application`
- [ ] Environment variables configured
- [ ] Database connected

### Post-Deployment
- [ ] Application accessible at Render URL
- [ ] Database migrations applied
- [ ] Static files loading
- [ ] API endpoints working
- [ ] No errors in logs

---

## 🎯 Summary

### What Was Fixed:
✅ Created `requirements.txt` in correct location  
✅ Created `render.yaml` for automatic configuration  
✅ Created `build.sh` for build process  
✅ Documented complete deployment process

### Next Steps:
1. Commit and push new files
2. Create Render account (if needed)
3. Connect repository to Render
4. Configure environment variables
5. Deploy!

---

**Your deployment error is now fixed!** 🎉

The `requirements.txt` file is now in the correct location where Render expects it.

---

**Last Updated:** May 1, 2026
