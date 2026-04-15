# FINAL HYBRID TASK DISTRIBUTION (v6 – REAL, BALANCED, BACKEND-ONLY)

🧠 SYSTEM BREAKDOWN (REAL DJANGO VIEW)
Views (API) → Services (Logic/AI) → Models (DB) → Events → WebSocket

Each member owns real files + real responsibilities.

👤 MEMBER 1 — Core Backend & Shared Infrastructure 🔗
🛠️ Owns (REAL FILES)
core/
  ├── responses.py
  ├── exceptions.py
  ├── validators.py
  ├── utils.py
🎯 Responsibilities
Standard API response format
Global exception handling
Shared validators (length, required fields)
Helper utilities used across modules
➕ Real Work Added
Integrate API responses across:
patients
dashboard
auth
🤝 Works With
M3, M4 (API formatting)
M5, M6 (service integration)
M8 (testing consistency)

👤 MEMBER 2 — Authentication & Security 🔐
🛠️ Owns
authentication/
  ├── models.py (User)
  ├── views.py
  ├── serializers.py
  ├── permissions.py
  ├── services/
🎯 Responsibilities
JWT login & refresh
Role system (patient/staff/admin)
Permission classes
WebSocket authentication middleware
➕ Real Work
Protect ALL endpoints
Role-based access enforcement
🤝 Works With
M3, M4 (API protection)
M7 (User model relations)
M8 (WS auth testing)

👤 MEMBER 3 — Patient API (Input Layer) 🧑
🛠️ Owns
patients/
  ├── views.py
  ├── serializers.py
🎯 Responsibilities
POST /api/triage/
Input validation (≤500 chars)
Start processing pipeline
Emit “new patient” event
➕ Real Work
Optional: patient history API
🤝 Works With
M5 (AI call)
M6 (logic)
M7 (DB)
M8 (event trigger)

👤 MEMBER 4 — Dashboard APIs (Output Layer) 📊
🛠️ Owns
dashboard/
  ├── views.py
  ├── serializers.py
🎯 Responsibilities
Staff:
patient queue
filtering
sorting
Admin:
overview stats
analytics
➕ Real Work
Aggregation queries (counts, averages)
🤝 Works With
M6 (logic data)
M7 (queries)
M2 (permissions)
M8 (real-time updates)

👤 MEMBER 5 — AI Service Layer 🧠
🛠️ Owns
triage/services/
  ├── ai_service.py
  ├── prompt_engine.py
🎯 Responsibilities
Call OpenAI/Gemini
Build prompts
Parse response
➕ Real Work
Retry mechanism
Timeout handling
🤝 Works With
M3 (input)
M6 (logic)
M1 (integration)

👤 MEMBER 6 — Triage Logic & Business Rules ⚙️
🛠️ Owns
triage/services/
  ├── triage_service.py
  ├── validation_service.py
🎯 Responsibilities
urgency score
priority mapping
fallback system
status transitions
➕ Real Work
critical alert logic
event triggers
🤝 Works With
M5 (AI output)
M7 (DB)
M4 (dashboard)
M8 (events)

👤 MEMBER 7 — Data Layer (Models & Queries) 🗄️
🛠️ Owns
patients/models.py
triage/models.py
authentication/models.py
🎯 Responsibilities
All models
relationships
migrations
optimized queries
➕ Real Work
Admin APIs (user + patient management)
🤝 Works With
M3 (store input)
M6 (store results)
M4 (fetch data)
M2 (roles)

👤 MEMBER 8 — Real-Time System & Backend Testing ⚡🧪
🛠️ Owns
realtime/
  ├── consumers.py
  ├── routing.py
  ├── services/broadcast_service.py
🎯 Responsibilities
Django Channels
Redis
WebSocket broadcasting
Backend testing (Postman, scripts)
➕ Real Work
Performance testing
Integration testing
🤝 Works With
M3 (submission event)
M6 (logic events)
M4 (payload structure)
M2 (security)
M1 (integration)

⚡ REAL-TIME DISTRIBUTION (FINAL FIXED)
Task	Owner
WebSocket setup	M8
Redis config	M8
Submission trigger	M3
Logic trigger	M6
Payload format	M4
Security	M2
Integration/debug	M1

👉 ✔ Shared properly
👉 ✔ No overload

🔄 FINAL SYSTEM FLOW (LOCKED)
1. POST /api/triage/       → M3
2. AI processing           → M5
3. Triage logic            → M6
4. Save to DB              → M7
5. Emit event              → M3/M6
6. WebSocket broadcast     → M8
7. Dashboard API fetch     → M4
---
