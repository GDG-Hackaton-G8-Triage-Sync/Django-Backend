#### Demographics in Registration
Registration accepts patient demographic and profile fields at signup. The following fields must be provided for patients: `name`, `email`, `password`, `role`, and `age`. Optional profile fields that can be included at registration and will be saved to the patient profile: `gender`, `blood_type`, `health_history`, `allergies`, `current_medications`, `bad_habits`.
# TriageSync - Intelligent Medical Triage System

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/Tests-44%2F44%20Passing-brightgreen.svg)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**TriageSync** is an AI-powered medical triage system that intelligently prioritizes patients based on symptom severity, ensuring critical cases receive immediate attention. Built for healthcare facilities to optimize patient flow and improve emergency response times.

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

### AI-Powered Triage
- **Google Gemini Integration**: Advanced AI analysis using multiple Gemini models
- **Multi-Model Fallback**: Automatic failover across gemini-2.5-flash and gemini-1.5-flash
- **Rule-Based Backup**: Keyword-based triage when AI is unavailable
- **PDF Support**: Extract and analyze symptoms from medical documents
- **Circuit Breaker**: Protects against API quota exhaustion
- **Blood Type Integration**: AI considers patient blood type for transfusion guidance in severe bleeding cases

### Intelligent Queue Management
- **Dynamic Priority Ordering**: Critical cases (Priority 1) automatically move to top
- **5-Level Priority System**: From life-threatening (1) to non-urgent (5)
- **Real-Time Updates**: WebSocket broadcasts for instant queue changes
- **FIFO Within Priority**: Fair ordering for patients with similar urgency
- **Special Case Handling**: Elevated priority for pregnancy, elderly, immunocompromised

### Secure Authentication
- **JWT-Based Auth**: Secure token-based authentication with refresh tokens
- **Role-Based Access Control**: Patient, Nurse, Doctor, Admin roles
- **Permission System**: Granular endpoint access control
- **Token Refresh**: Automatic token renewal for seamless sessions

### Real-Time Communication
- **WebSocket Events**: Live updates for staff dashboards
- **Event Types**: Patient created, priority updates, critical alerts, status changes
- **Role-Based Access**: Medical staff only (doctors, nurses, admins)
- **Auto-Reconnection**: Handles connection drops gracefully

### Notification System
- **Real-Time Notifications**: Instant WebSocket delivery to user-specific channels
- **Persistent Storage**: Database-backed notification history with read/unread tracking
- **User Preferences**: Granular opt-out controls per notification type
- **5 Notification Types**: Triage status changes, priority updates, role changes, critical alerts, system messages
- **Smart Routing**: Priority-based staff notifications (critical → supervisors/doctors, high → doctors/supervisors, medium → nurses/doctors)
- **Bulk Notifications**: System-wide alerts for maintenance, emergencies, and queue management
- **Integration**: Automatic notifications for triage submissions, status updates, staff assignments, and role changes

### Comprehensive Dashboard
- **Patient Queue**: Sortable, filterable list with pagination (20 per page, max 100)
- **Analytics**: System-wide statistics and trends
- **Status Management**: Update patient workflow status (waiting → in_progress → completed)
- **Priority Override**: Manual priority adjustments when needed

## System Requirements

### Required
- **Python**: 3.14 or higher
- **PostgreSQL**: 14+ (or SQLite for development)
- **pip**: Latest version
- **Virtual Environment**: venv or virtualenv

### Optional
- **Redis**: For production caching (recommended)
- **Nginx**: For production deployment
- **Docker**: For containerized deployment

## Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/triagesync.git
cd triagesync/Django-Backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp triagesync_backend/.env.example triagesync_backend/.env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Server will start at `http://localhost:8000`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/triagesync.git
cd triagesync/Django-Backend
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create `.env` file in `triagesync_backend/` directory:

```env
# Django Settings
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here-generate-with-django
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL only - required)
DATABASE_URL=postgresql://user:password@localhost:5432/triagesync

# Gemini AI (Required)
GEMINI_API_KEY=your-gemini-api-key-here

# CORS (for frontend)
CORS_ALLOW_ALL_ORIGINS=True
```

**Generate Django Secret Key:**
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 5. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Access the application:
- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DJANGO_DEBUG` | Enable debug mode | `False` | No |
| `DJANGO_SECRET_KEY` | Django secret key | - | **Yes** |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | `localhost` | **Yes** |
| `DATABASE_URL` | PostgreSQL connection string | - | **Yes** |
| `GEMINI_API_KEY` | Google Gemini API key | - | **Yes** |
| `CORS_ALLOW_ALL_ORIGINS` | Allow all CORS origins | `False` | No |

### AI Service Configuration

Configure in `triagesync_backend/config/settings.py`:

```python
# Gemini AI Settings
GEMINI_MODEL_PRIORITY = [
    "gemini-2.5-flash",      # Primary model
    "gemini-1.5-flash"       # Fallback model
]
GEMINI_MAX_RETRIES = 2
GEMINI_TIMEOUT_SECONDS = 8
GEMINI_CIRCUIT_BREAKER_THRESHOLD = 5
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 30
GEMINI_MODEL_LIST_TTL_SECONDS = 600

# Triage Priority Thresholds
PRIORITY_THRESHOLDS = {
    "critical": 80,  # Priority 1 (life-threatening)
    "high": 60,      # Priority 2 (emergent)
    "medium": 40,    # Priority 3 (urgent)
    "low": 20,       # Priority 4 (semi-urgent)
                     # Priority 5 (non-urgent, < 20)
}

# Triage Fallback (when AI unavailable)
TRIAGE_FALLBACK = {
    "priority": 3,
    "urgency_score": 50,
    "condition": "Unknown - Staff Review Required"
}
```

## Project Structure

```
Django-Backend/
├── triagesync_backend/          # Main Django project
│   ├── apps/                    # Django applications
│   │   ├── authentication/      # User auth & JWT
│   │   │   ├── models.py        # User model with roles
│   │   │   ├── views.py         # Login, register, refresh, logout
│   │   │   ├── permissions.py   # Role-based permissions
│   │   │   ├── serializers.py   # Auth serializers
│   │   │   └── tests/           # Authentication tests
│   │   │
│   │   ├── patients/            # Patient management
│   │   │   ├── models.py        # Patient, PatientSubmission models
│   │   │   ├── views.py         # Profile, history, submissions
│   │   │   ├── serializers.py   # Patient serializers
│   │   │   └── tests/           # Patient tests
│   │   │
│   │   ├── triage/              # AI triage service
│   │   │   ├── services/
│   │   │   │   ├── ai_service.py         # Gemini integration
│   │   │   │   ├── triage_service.py     # Business logic
│   │   │   │   ├── prompt_engine.py      # AI prompts
│   │   │   │   ├── validation_service.py # Input validation
│   │   │   │   └── triage_config.py      # Configuration
│   │   │   ├── views.py         # Triage endpoints
│   │   │   ├── serializers.py   # Triage serializers
│   │   │   └── tests/           # Triage tests
│   │   │
│   │   ├── dashboard/           # Staff dashboard
│   │   │   ├── services/
│   │   │   │   └── dashboard_service.py  # Queue management
│   │   │   ├── views.py         # Dashboard endpoints
│   │   │   ├── serializers.py   # Dashboard serializers
│   │   │   └── tests/           # Dashboard tests
│   │   │
│   │   ├── realtime/            # WebSocket events
│   │   │   ├── consumers.py     # WebSocket consumer
│   │   │   ├── routing.py       # WebSocket routing
│   │   │   ├── services/
│   │   │   │   ├── broadcast_service.py  # Event broadcasting
│   │   │   │   └── event_service.py      # Event builders
│   │   │   └── tests.py         # WebSocket tests
│   │   │
│   │   ├── notifications/       # Notification system
│   │   │   ├── models.py        # Notification, NotificationPreference
│   │   │   ├── views.py         # Notification endpoints
│   │   │   ├── serializers.py   # Notification serializers
│   │   │   ├── services/
│   │   │   │   ├── notification_service.py        # Core notification service
│   │   │   │   └── system_notification_service.py # System-wide notifications
│   │   │   ├── management/
│   │   │   │   └── commands/
│   │   │   │       └── test_notifications.py      # Test command
│   │   │   └── tests/           # Notification tests (48 tests)
│   │   │
│   │   └── core/                # Shared utilities
│   │       ├── pagination.py    # Pagination classes
│   │       ├── response.py      # Response helpers
│   │       ├── validators.py    # Input validators
│   │       └── constants.py     # Shared constants
│   │
│   ├── config/
│   │   ├── settings.py          # Django settings
│   │   ├── urls.py              # URL routing
│   │   ├── asgi.py              # ASGI config (WebSocket)
│   │   └── wsgi.py              # WSGI config
│   │
│   └── .env                     # Environment variables
│
├── docs/                        # Documentation
│   ├── API_DOCUMENTATION.md     # Complete API reference
│   ├── AI_SERVICE_USAGE_GUIDE.md
│   └── QUEUE_PRIORITY_SYSTEM_DOCUMENTATION.md
│
├── tests/                       # Integration tests
├── fixtures/                    # Sample data
├── manage.py                    # Django management
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest configuration
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

#### Demographics in AI Endpoints
If authenticated, the system automatically uses the patient's saved age, gender, and blood type for AI analysis (no need to send them in the request body). If unauthenticated, you may provide `age`, `gender`, and `blood_type` directly in the request.

**Blood Type Support**: The AI triage system now accepts blood type as a demographic parameter. When severe bleeding or hemorrhage is detected, the AI provides blood transfusion guidance:
- **Known Blood Type**: Recommends compatible blood types for transfusion based on ABO and Rh compatibility rules
- **Unknown Blood Type**: Recommends urgent blood typing and crossmatch
- **Non-Bleeding Cases**: Blood type is included in analysis but no transfusion guidance is provided

**Supported Blood Types**: A+, A-, B+, B-, AB+, AB-, O+, O-

### Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://django-backend-4r5p.onrender.com`

### Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Quick API Examples

**1. Register a new user:**
```bash
POST /api/v1/auth/register/
Content-Type: application/json

{
  "name": "john_doe",
  "email": "john@example.com",
  "password": "secure_password123",
  "password2": "secure_password123",
  "role": "patient",
  "age": 35,
  "gender": "male",
  "blood_type": "A+"
}
```

**2. Login:**
```bash
POST /api/v1/auth/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "role": "patient",
  "user_id": 1,
  "name": "john_doe",
  "email": "john@example.com"
}
```

**3. Submit triage request:**
```bash
POST /api/v1/triage/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "description": "Chest pain and shortness of breath"
}

Response:
{
  "id": 123,
  "description": "Chest pain and shortness of breath",
  "priority": 1,
  "urgency_score": 95,
  "condition": "Acute Cardiac Event",
  "status": "waiting",
  "created_at": "2026-04-29T08:00:00Z"
}
```

**4. Get user notifications:**
```bash
GET /api/v1/notifications/
Authorization: Bearer <access_token>

Response:
{
  "data": [
    {
      "id": 1,
      "notification_type": "triage_status_change",
      "title": "Your Case is Being Reviewed",
      "message": "Medical staff are now reviewing your triage submission (ID: 123).",
      "metadata": {
        "submission_id": 123,
        "priority": 2,
        "condition": "High fever"
      },
      "is_read": false,
      "created_at": "2026-04-30T08:00:00Z",
      "read_at": null
    }
  ]
}
```

**5. Mark notification as read:**
```bash
PATCH /api/v1/notifications/1/read/
Authorization: Bearer <access_token>

Response:
{
  "data": {
    "id": 1,
    "is_read": true,
    "read_at": "2026-04-30T08:15:00Z"
  }
}
```

**6. Submit triage with blood type (for severe bleeding cases):**
```bash
POST /api/v1/triage/ai/
Content-Type: application/json

{
  "symptoms": "Severe bleeding from leg wound after accident",
  "age": 35,
  "gender": "male",
  "blood_type": "A+"
}

Response:
{
  "priority_level": 1,
  "urgency_score": 95,
  "condition": "Severe Hemorrhage",
  "category": "Trauma",
  "is_critical": true,
  "explanation": ["severe bleeding", "trauma"],
  "recommended_action": "Immediate hemorrhage control. Compatible blood types for transfusion: A+, A-, O+, O-",
  "reason": "Life-threatening blood loss requires immediate intervention",
  "source": "ai"
}
```

### API Endpoints Overview

| Category | Endpoint | Method | Auth | Description |
|----------|----------|--------|------|-------------|
| **Authentication** |
| | `/api/v1/auth/register/` | POST | No | Register new user |
| | `/api/v1/auth/login/` | POST | No | Login and get tokens |
| | `/api/v1/auth/refresh/` | POST | No | Refresh access token |
| | `/api/v1/auth/logout/` | POST | Yes | Logout (blacklist token) |
| | `/api/v1/profile/` | GET | Yes | Get user profile |
| **Triage** |
| | `/api/v1/triage/` | POST | Patient | Submit triage request |
| | `/api/v1/triage/ai/` | POST | No | AI analysis only |
| | `/api/v1/triage/pdf-extract/` | POST | No | PDF symptom extraction |
| | `/api/v1/triage/ai/` | POST | Yes/No | AI analysis (uses patient profile age/gender if authenticated) |
| **Patient** |
| | `/api/v1/patients/profile/` | GET | Patient | Get patient profile |
| | `/api/v1/patients/profile/` | PATCH | Patient | Update patient profile |
| | `/api/v1/patients/history/` | GET | Patient | Get submission history |
| | `/api/v1/patients/submissions/{id}/` | GET | Patient | Get submission details |
| | `/api/v1/patients/current/` | GET | Patient | Get active session |
| **Dashboard (Staff)** |
| | `/api/v1/dashboard/staff/patients/` | GET | Staff | Get patient queue |
| | `/api/v1/dashboard/staff/patient/{id}/status/` | PATCH | Staff | Update patient status |
| | `/api/v1/dashboard/staff/patient/{id}/priority/` | PATCH | Staff | Update priority |
| | `/api/v1/dashboard/staff/patient/{id}/verify/` | PATCH | Staff | Verify patient |
| | `/api/v1/admin/overview/` | GET | Staff | System overview |
| | `/api/v1/admin/analytics/` | GET | Staff | System analytics |
| **WebSocket** |
| | `/ws/triage/events/` | WS | Staff | Real-time events |
| **Notifications** |
| | `/api/v1/notifications/` | GET | Yes | List user notifications |
| | `/api/v1/notifications/{id}/read/` | PATCH | Yes | Mark notification as read |
| | `/api/v1/notifications/read-all/` | PATCH | Yes | Mark all as read |
| | `/api/v1/notifications/unread-count/` | GET | Yes | Get unread count |

**For complete API documentation with request/response examples, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)**

## Testing

### Run All Tests

```bash
# Run all Django tests with parallel execution
python manage.py test --parallel

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Run Specific Tests

```bash
# Test specific app
python manage.py test triagesync_backend.apps.triage

# Test specific file
python manage.py test triagesync_backend.apps.triage.tests.test_triage_service

# Test specific test case
python manage.py test triagesync_backend.apps.triage.tests.test_triage_service.TriageServiceTests.test_emergency_override
```

### Verification Scripts

```bash
# Verify AI service functionality
python verify_ai_service_complete.py

# Verify queue priority ordering
python verify_queue_priority_ordering.py
```

### Test Results

- **Total Tests**: 92 (44 core + 48 notification)
- **Passing**: 92 (100%)
- **Coverage**: 85%+
- **Test Execution Time**: ~350 seconds

### Test Categories

- Authentication & Authorization (8 tests)
- API Contract Compliance (5 tests)
- Dashboard & Queue Management (7 tests)
- Error Handling (3 tests)
- Patient Endpoints (6 tests)
- Triage Service (10 tests)
- WebSocket Events (5 tests)
- **Notification System (48 tests)**
  - Integration Tests (14 tests)
  - Triage Integration (8 tests)
  - Patient Service Integration (11 tests)
  - Core Service Tests (15 tests)

## Deployment

### Production Checklist

- [ ] Set `DJANGO_DEBUG=False`
- [ ] Generate strong `DJANGO_SECRET_KEY`
- [ ] Configure `DJANGO_ALLOWED_HOSTS` with your domain
- [ ] Set up PostgreSQL database
- [ ] Configure `GEMINI_API_KEY`
- [ ] Set up Redis for caching
- [ ] Configure CORS settings for your frontend domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure static file serving (Whitenoise or CDN)
- [ ] Set up logging and monitoring (Sentry, etc.)
- [ ] Configure backup strategy for database
- [ ] Set up CI/CD pipeline

### Deploy to Render

1. **Create `render.yaml`** in project root:

```yaml
services:
  - type: web
    name: triagesync-backend
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: gunicorn triagesync_backend.config.wsgi:application
    envVars:
      - key: DJANGO_SECRET_KEY
        generateValue: true
      - key: DJANGO_DEBUG
        value: False
      - key: DJANGO_ALLOWED_HOSTS
        value: triagesync-backend.onrender.com
      - key: DATABASE_URL
        fromDatabase:
          name: triagesync-db
          property: connectionString
      - key: GEMINI_API_KEY
        sync: false

databases:
  - name: triagesync-db
    databaseName: triagesync
    user: triagesync
```

2. **Push to GitHub**
3. **Connect repository to Render**
4. **Configure environment variables** in Render dashboard
5. **Deploy**

### Deploy with Docker

```dockerfile
# Dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "triagesync_backend.config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```bash
# Build image
docker build -t triagesync-backend .

# Run container
docker run -p 8000:8000 \
  -e DJANGO_SECRET_KEY=your-secret \
  -e DATABASE_URL=postgresql://... \
  -e GEMINI_API_KEY=your-key \
  triagesync-backend
```

### Deploy with Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: triagesync
      POSTGRES_USER: triagesync
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn triagesync_backend.config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SECRET_KEY=your-secret-key
      - DATABASE_URL=postgresql://triagesync:secure_password@db:5432/triagesync
      - GEMINI_API_KEY=your-gemini-key
    depends_on:
      - db

volumes:
  postgres_data:
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'triagesync_backend'`

```bash
# Solution: Ensure you're in the Django-Backend directory
cd Django-Backend
python manage.py runserver
```

**Issue**: `django.db.utils.OperationalError: FATAL: password authentication failed`

```bash
# Solution: Check DATABASE_URL in .env file
# Ensure PostgreSQL is running and credentials are correct
# Test connection:
psql -h localhost -U your_user -d triagesync
```

**Issue**: `AI service unavailable` or `503 Service Unavailable`

```bash
# Solution: Check GEMINI_API_KEY in .env
# Verify API key is valid: python verify_ai_service_complete.py
# Check API quota in Google Cloud Console
# Verify internet connection
```

**Issue**: `WebSocket connection failed`

```bash
# Solution: Ensure ASGI server is running (Daphne/Uvicorn)
# Check WebSocket URL format: ws://localhost:8000/ws/triage/events/?token=<JWT>
# Verify user has staff role (patient role not authorized for WebSocket)
# Check JWT token is valid and not expired
```

**Issue**: `UnicodeEncodeError` when running tests

```bash
# Solution: Windows encoding issue with emoji characters
# Run: python fix_test_unicode.py
# This replaces Unicode characters with ASCII equivalents
```

**Issue**: Tests failing with `ValueError: Priority must be an integer between 1 and 5`

```bash
# Solution: Already fixed in latest version
# Ensure you have the latest code with type conversion in UpdatePatientPriorityView
```

## Additional Documentation

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference with examples
- **[AI_SERVICE_USAGE_GUIDE.md](AI_SERVICE_USAGE_GUIDE.md)** - AI service configuration and usage
- **[QUEUE_PRIORITY_SYSTEM_DOCUMENTATION.md](QUEUE_PRIORITY_SYSTEM_DOCUMENTATION.md)** - Queue ordering details
- **[TEST_FIXES_SUMMARY.md](TEST_FIXES_SUMMARY.md)** - Testing procedures and fixes
- **[NOTIFICATION_SYSTEM_INTEGRATION_SUMMARY.md](NOTIFICATION_SYSTEM_INTEGRATION_SUMMARY.md)** - Notification system integration guide
- **[NOTIFICATION_TESTS_SUMMARY.md](NOTIFICATION_TESTS_SUMMARY.md)** - Notification test results and coverage

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features (maintain 85%+ coverage)
- Update documentation for API changes
- Ensure all tests pass before submitting PR
- Use meaningful commit messages

### Code Style

```bash
# Format code with black
black .

# Check linting with flake8
flake8 .

# Sort imports with isort
isort .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Team

- **Backend Development**: Django REST Framework, AI Integration, WebSocket
- **Frontend Development**: React/Vue.js (separate repository)
- **DevOps**: Deployment, CI/CD, Infrastructure
- **QA**: Testing, Quality Assurance

## Acknowledgments

- **Google Gemini AI** for intelligent triage analysis
- **Django** and **Django REST Framework** communities
- **Channels** for WebSocket support
- All contributors and testers

## Support

- **Email**: support@triagesync.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/triagesync/issues)
- **Documentation**: [Full Documentation](https://docs.triagesync.com)

---

**Built with ❤️ for better healthcare**

**Version**: 1.2.0  
**Last Updated**: April 30, 2026  
**Status**: Production Ready ✅
