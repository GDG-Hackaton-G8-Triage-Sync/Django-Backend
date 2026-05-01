# TriageSync Backend - Production Deployment Guide

## 📋 Table of Contents
1. [Environment Configuration](#environment-configuration)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Steps](#deployment-steps)
4. [Security Hardening](#security-hardening)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Environment Configuration

### Required Environment Variables

Your `.env` file must contain these essential variables:

```bash
# Django Core
DJANGO_SECRET_KEY=<random-secret-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-domain.com>

# Database (PostgreSQL required)
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require

# CORS
CORS_ALLOW_ALL_ORIGINS=False

# AI Service
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL_PRIORITY=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash
GEMINI_MAX_RETRIES=2
GEMINI_TIMEOUT_SECONDS=8
GEMINI_MODEL_LIST_TTL_SECONDS=600
GEMINI_CIRCUIT_BREAKER_THRESHOLD=5
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30

# Redis (Optional - for WebSocket support)
# REDIS_URL=redis://localhost:6379/0
```

### Environment Files

We provide three environment file templates:

1. **`.env.example`** - Template (safe to commit to git)
2. **`.env.production`** - Production template with documentation
3. **`.env`** - Your actual configuration (never commit!)

---

## ✅ Pre-Deployment Checklist

### 1. Security Configuration

- [ ] **Generate new SECRET_KEY**
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

- [ ] **Set DEBUG=False**
  ```bash
  DJANGO_DEBUG=False
  ```

- [ ] **Configure ALLOWED_HOSTS**
  ```bash
  DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
  ```

- [ ] **Disable CORS_ALLOW_ALL_ORIGINS**
  ```bash
  CORS_ALLOW_ALL_ORIGINS=False
  ```
  Then configure specific origins in `settings.py`:
  ```python
  CORS_ALLOWED_ORIGINS = [
      "https://yourdomain.com",
      "https://www.yourdomain.com",
  ]
  ```

### 2. Database Configuration

- [ ] **PostgreSQL database created**
- [ ] **Database user with proper permissions**
- [ ] **SSL/TLS enabled** (`sslmode=require`)
- [ ] **Connection pooling configured** (recommended)
- [ ] **Backup strategy in place**

### 3. API Keys & Services

- [ ] **Valid Gemini API key** with sufficient quota
- [ ] **Redis configured** (if using WebSocket features)
- [ ] **API rate limits understood** (15 req/min, 1500 req/day for free tier)

### 4. Static & Media Files

- [ ] **Static files collected**
  ```bash
  python manage.py collectstatic --noinput
  ```

- [ ] **Media directory configured** with proper permissions
- [ ] **Web server configured** to serve static/media files

### 5. Database Migrations

- [ ] **All migrations applied**
  ```bash
  python manage.py migrate
  ```

- [ ] **Superuser created** (if needed)
  ```bash
  python manage.py createsuperuser
  ```

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment

```bash
# Clone repository
git clone <your-repo-url>
cd Django-Backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.production triagesync_backend/.env

# Edit .env with your production values
nano triagesync_backend/.env
```

**Critical changes:**
- Generate new `DJANGO_SECRET_KEY`
- Set `DJANGO_DEBUG=False`
- Update `DJANGO_ALLOWED_HOSTS`
- Configure `DATABASE_URL`
- Set `CORS_ALLOW_ALL_ORIGINS=False`
- Add your `GEMINI_API_KEY`

### Step 3: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Verify database connection
python manage.py check --database default
```

### Step 4: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 5: Test Configuration

```bash
# Run system checks
python manage.py check --deploy

# Test server (development mode)
python manage.py runserver

# Run tests
pytest
```

### Step 6: Deploy with Production Server

#### Option A: Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn triagesync_backend.config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile -
```

#### Option B: uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Run with uWSGI
uwsgi --http :8000 \
  --module triagesync_backend.config.wsgi:application \
  --master \
  --processes 4 \
  --threads 2
```

### Step 7: Configure Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /path/to/staticfiles/;
        expires 30d;
    }

    # Media files
    location /media/ {
        alias /path/to/media/;
        expires 7d;
    }

    # Proxy to Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (if using)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Step 8: Configure Systemd Service (Linux)

Create `/etc/systemd/system/triagesync.service`:

```ini
[Unit]
Description=TriageSync Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/Django-Backend
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/gunicorn \
  triagesync_backend.config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 30
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable triagesync
sudo systemctl start triagesync
sudo systemctl status triagesync
```

---

## 🔒 Security Hardening

### 1. Environment Variables

- ✅ Never commit `.env` files to version control
- ✅ Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
- ✅ Rotate credentials regularly
- ✅ Use strong, random passwords

### 2. Django Security Settings

Add to `settings.py` for production:

```python
# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 3. Database Security

- ✅ Use SSL/TLS for database connections
- ✅ Restrict database access by IP
- ✅ Use strong passwords
- ✅ Regular backups
- ✅ Enable audit logging

### 4. API Security

- ✅ Rate limiting configured
- ✅ JWT tokens with short expiration
- ✅ CORS properly configured
- ✅ Input validation enabled
- ✅ SQL injection protection (Django ORM)

### 5. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

---

## 📊 Monitoring & Maintenance

### 1. Logging

Configure logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/triagesync/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### 2. Health Checks

Create a health check endpoint:

```python
# In urls.py
path('health/', lambda request: JsonResponse({'status': 'ok'}))
```

### 3. Monitoring Tools

- **Application Performance**: New Relic, DataDog, Sentry
- **Server Monitoring**: Prometheus, Grafana
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **Log Management**: ELK Stack, Splunk

### 4. Backup Strategy

```bash
# Database backup (daily cron job)
0 2 * * * pg_dump -h host -U user dbname | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz

# Retention: Keep 30 days
find /backups -name "db_*.sql.gz" -mtime +30 -delete
```

### 5. Regular Maintenance

- [ ] **Weekly**: Review logs for errors
- [ ] **Monthly**: Update dependencies
- [ ] **Quarterly**: Security audit
- [ ] **Annually**: Rotate credentials

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check STATIC_ROOT in settings.py
# Verify nginx configuration
```

#### 2. Database Connection Errors

```bash
# Test connection
python manage.py check --database default

# Verify DATABASE_URL format
# Check firewall rules
# Verify SSL/TLS settings
```

#### 3. AI Endpoint 503 Errors

```bash
# Check Gemini API quota
# Verify GEMINI_API_KEY
# Review circuit breaker settings
# Check logs for specific errors
```

#### 4. CORS Errors

```bash
# Verify CORS_ALLOWED_ORIGINS in settings.py
# Check CORS_ALLOW_ALL_ORIGINS setting
# Review browser console for specific errors
```

#### 5. WebSocket Connection Issues

```bash
# Verify Redis is running
# Check REDIS_URL configuration
# Review nginx WebSocket proxy settings
```

### Debug Mode (Temporary)

If you need to enable debug mode temporarily:

```bash
# Set in .env
DJANGO_DEBUG=True

# Restart service
sudo systemctl restart triagesync

# IMPORTANT: Set back to False after debugging!
```

### Logs Location

```bash
# Application logs
tail -f /var/log/triagesync/error.log

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Systemd logs
sudo journalctl -u triagesync -f
```

---

## 📞 Support

For issues or questions:
- Check logs first
- Review this deployment guide
- Consult Django documentation: https://docs.djangoproject.com/
- Check Gemini API docs: https://ai.google.dev/docs

---

## 📝 Version History

- **v1.0** - Initial production deployment guide
- Includes all essential configuration
- Security hardening recommendations
- Monitoring and maintenance procedures

---

**Last Updated:** May 1, 2026
