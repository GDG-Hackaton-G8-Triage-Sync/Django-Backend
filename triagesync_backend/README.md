# TriageSync Backend

Professional Django backend scaffold for a medical triage platform.

## Stack
- Django
- Django REST Framework
- JWT authentication (SimpleJWT)
- Django Channels (WebSocket support)

## Quick Start
1. Create and activate virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Apply migrations:
   python manage.py migrate
4. Run server:
   python manage.py runserver

## Project Layout
- config: central Django configuration (settings, URLs, ASGI/WSGI)
- apps.authentication: user and auth flows
- apps.patients: patient submission flows
- apps.triage: triage analysis and validation services
- apps.realtime: websocket consumers and event broadcasting
- apps.dashboard: dashboard and patient listing APIs
- apps.core: shared constants, exceptions, middleware, and response helpers

---

# 🏗️ 🧠 FINAL DJANGO BACKEND STRUCTURE (UPDATED)

```text
triagesync_backend/
├── config/                          # PROJECT CONFIGURATION
│   ├── __init__.py
│   ├── settings.py                  # JWT, DRF, Channels, DB config
│   ├── urls.py                     # Root routes
│   ├── asgi.py                     # WebSocket entry (Channels)
│   ├── wsgi.py
│
├── apps/                            # ALL APPLICATION MODULES
│
│ ├── authentication/               🔐 AUTH MODULE (Member 1 + 2)
│ │   ├── models.py                 # Custom User model (role-based)
│ │   ├── admin.py
│ │   ├── apps.py
│ │   ├── urls.py
│ │   ├── views.py                  # login endpoint
│ │   ├── serializers.py            # login/register validation
│ │   ├── permissions.py            # role-based access
│ │   ├── services/
│ │   │   ├── auth_service.py       # JWT logic, token handling
│ │   │   └── user_service.py
│ │   └── tests.py
│
│ ├── patients/                     🧑 PATIENT MODULE (Member 3 + 4)
│ │   ├── models.py                 # Patient submission model
│ │   ├── urls.py
│ │   ├── views.py                  # /api/triage/
│ │   ├── serializers.py            # input validation (500 chars)
│ │   ├── services/
│ │   │   ├── patient_service.py    # submit symptom logic
│ │   │   └── history_service.py
│ │   └── tests.py
│
│ ├── triage/                       🧠 AI + DECISION ENGINE
│ │   ├── models.py                 # TriageResult model
│ │   ├── urls.py
│ │   ├── views.py                  # connects AI → response
│ │   ├── serializers.py
│ │   ├── services/                 # CORE INTELLIGENCE LAYER
│ │   │   ├── ai_service.py         # OpenAI/Gemini API call (Member 5)
│ │   │   ├── triage_service.py     # priority + urgency logic (Member 6)
│ │   │   ├── validation_service.py # JSON validation + fallback
│ │   │   └── prompt_engine.py      # AI prompt templates
│ │   └── tests.py
│
│ ├── realtime/                     ⚡ REAL-TIME SYSTEM (Member 8)
│ │   ├── consumers.py              # WebSocket consumer (Channels)
│ │   ├── routing.py                # WS routing
│ │   ├── urls.py
│ │   ├── services/
│ │   │   ├── broadcast_service.py  # send updates to dashboard
│ │   │   └── event_service.py      # event formatting
│ │   └── tests.py
│
│ ├── dashboard/                    📊 DASHBOARD DATA API (Member 4)
│ │   ├── views.py                  # GET /api/patients/
│ │   ├── urls.py
│ │   ├── serializers.py
│ │   ├── services/
│ │   │   ├── dashboard_service.py  # sorting + filtering logic
│ │   └── tests.py
│
│ ├── core/                         🧰 SHARED UTILITIES
│ │   ├── utils.py
│ │   ├── constants.py
│ │   ├── exceptions.py
│ │   ├── response.py               # standard API response format
│ │   └── middleware.py
│
├── requirements.txt
├── manage.py
└── README.md
```

---


