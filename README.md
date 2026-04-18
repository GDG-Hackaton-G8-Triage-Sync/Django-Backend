# Django-Backend
TriageSync Backend
🚀 Deployed Backend
Production: https://django-backend-4r5p.onrender.com/

Professional Django backend scaffold for a medical triage platform.

##Stack
Django
Django REST Framework
JWT authentication (SimpleJWT)
Django Channels (WebSocket support)


##Quick Start
Create and activate virtual environment.
Install dependencies: pip install -r requirements.txt
Apply migrations: python manage.py migrate
Run server: python manage.py runserver


##Project Layout
config: central Django configuration (settings, URLs, ASGI/WSGI)
apps.authentication: user and auth flows
apps.patients: patient submission flows
apps.triage: triage analysis and validation services
apps.realtime: websocket consumers and event broadcasting
apps.dashboard: dashboard and patient listing APIs
apps.core: shared constants, exceptions, middleware, and response helpers
