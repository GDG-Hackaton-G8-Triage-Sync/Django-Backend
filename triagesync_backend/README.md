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

# 👥 TEAM ROLES & FEATURE DISTRIBUTION

_See full breakdown in the project documentation or below for member responsibilities, collaboration flows, and fairness checks._

# 👥 TEAM ASSIGNMENT & FEATURE DISTRIBUTION


## Member Roles & Responsibilities

- **Member 1 — Backend Lead + API Architect**
  - System architecture, API contract design, code review & integration
  - Collaborates with Member 2 (Auth) and Member 6 (API)
- **Member 2 — Authentication & Security 🔐**
  - JWT authentication, role-based access, protected endpoints
  - Collaborates with Member 1 (Lead), Member 6 (API), Member 7 (WebSocket)
- **Member 3 — AI Integration Engineer 🧠**
  - AI API (OpenAI/Gemini), prompt engineering, raw response handling
  - Collaborates with Member 4 (Triage Logic), Member 5 (Validation)
- **Member 4 — Triage Logic Engineer ⚙️**
  - Urgency scoring, priority mapping, core triage processing
  - Collaborates with Member 3 (AI), Member 5 (Validation), Member 6 (API)
- **Member 5 — Validation + Database Engineer 🗄️**
  - JSON validation, fallback logic, database models & migrations
  - Collaborates with Member 3 (AI), Member 4 (Logic), Member 6 (API)
- **Member 6 — API Development Engineer 🌐**
  - Build endpoints, connect services, integration
  - Collaborates with Member 1 (Lead), Member 2 (Auth), Member 4 (Logic), Member 5 (DB), Member 7 (WebSocket)
- **Member 7 — Real-Time System Engineer ⚡**
  - Django Channels, WebSocket consumers, Redis integration
  - Collaborates with Member 6 (API), Member 2 (Auth), Member 8 (Testing)
- **Member 8 — Integration & Testing Engineer 🧪**
  - End-to-end testing, API & WebSocket testing, debugging
  - Collaborates with Member 7 (WebSocket), Member 6 (API), Member 4 (Logic), all members

## Key Collaboration Groups

- **AI + Processing Group:** Member 3 (AI), Member 4 (Logic), Member 5 (Validation)
  - _Flow:_ AI → Validation → Logic
- **API + Backend Core Group:** Member 1 (Lead), Member 6 (API), Member 2 (Auth)
  - _Flow:_ Request → Auth → API → Service
- **Real-Time Group:** Member 7 (WebSocket), Member 6 (API), Member 8 (Testing)
  - _Flow:_ DB save → Broadcast → Dashboard
- **Integration Group:** Member 8 (Lead), all members support
  - _Flow:_ Everything → Tested → Fixed

## Workload Balance Table

| Member | Work Type         | Load        | Status |
|--------|-------------------|-------------|--------|
| 1      | Design + Lead     | Medium      | ✅     |
| 2      | Auth              | Medium      | ✅     |
| 3      | AI                | Medium      | ✅     |
| 4      | Logic             | Medium      | ✅     |
| 5      | DB + Validation   | Medium      | ✅     |
| 6      | API               | Medium-High | ✅     |
| 7      | WebSocket         | Medium      | ✅     |
| 8      | Testing           | Medium      | ✅     |

- ✔ Fair distribution
- ✔ Shared responsibility in heavy areas
- ✔ No bottlenecks

## Feature-Based Task Distribution

Each member owns a feature slice across:
- models
- services
- views
- serializers

This ensures independence and balanced work.

## Feature Flow (How They Connect)

```
Login (M1, M2)
   ↓
Submit Symptoms (M3)
   ↓
AI Processing (M4)
   ↓
Validation + Logic (M5)
   ↓
Save Data (M6)
   ↓
WebSocket Broadcast (M7)
   ↓
Dashboard API (M8)
```

## Layered Team Structure (Hybrid Model)

- **Layer 1: Auth & Security (2 Members)**
  - Member 1: Auth Core (Login API, JWT, User model)
  - Member 2: Authorization & Protection (Role-based access, Permissions, WebSocket auth)
- **Layer 2: API Layer (2 Members)**
  - Member 3: Patient APIs (/api/triage/, input validation)
  - Member 4: Dashboard APIs (/api/patients/, sorting & response formatting)
- **Layer 3: Service Layer (2 Members)**
  - Member 5: AI Service (OpenAI/Gemini, prompt + response)
  - Member 6: Triage Logic Service (validation, urgency score, fallback logic)
- **Layer 4: Data Layer (1 Member + Support)**
  - Member 7: Database Engineer (models, migrations, relationships)
- **Layer 5: Real-Time System (1 Member + Support)**
  - Member 8: WebSocket Engineer (Django Channels, Redis, live updates)
- **Layer 6: Integration (Shared)**
  - Everyone contributes, led by Member 1 (Lead) and Member 8 (Testing)

## Why This Approach?

- ✔ Parallel development: Everyone can work independently
- ✔ Less blocking: No waiting for other modules
- ✔ Clear ownership: Each feature = one owner
- ✔ Easier debugging: You know exactly who owns what
- ✔ Keeps Django clean: apps + services respected
- ✔ Keeps team fast: parallel development
- ✔ Keeps features connected: not isolated
- ✔ Prevents chaos: clearer than feature-based only

---

# 🧑‍💻 TEAM ASSIGNMENT: SEPARATE FEATURE-BASED APPROACH

## Member-by-Member Feature Ownership

### 👤 MEMBER 1 — Authentication Feature 🔐
- Owns: Login system, JWT token generation, Role system
- Works on: authentication/models.py, authentication/services/auth_service.py, authentication/views.py, permissions.py
- Output: /api/login/, Token validation

### 👤 MEMBER 2 — Authorization + Route Protection 🔒
- Owns: Role-based access control, Protected endpoints, WebSocket auth
- Works on: permissions.py, middleware, DRF settings
- Output: Secured APIs, Block unauthorized access

### 👤 MEMBER 3 — Symptom Submission Feature 🧑
- Owns: Patient input handling
- Works on: patients/views.py, patients/serializers.py
- Responsibilities: Validate input (500 chars), Call triage service

### 👤 MEMBER 4 — AI Processing Feature 🧠
- Owns: AI API integration
- Works on: triage/services/ai_service.py
- Responsibilities: Send prompt, Receive raw AI output

### 👤 MEMBER 5 — Triage Logic + Validation ⚙️
- Owns: AI result validation, Priority + urgency calculation, fallback logic
- Works on: triage/services/triage_service.py, validation_service.py

### 👤 MEMBER 6 — Data Management (DB + Storage) 🗄️
- Owns: All models, Data storage, relations
- Works on: models.py across apps
- Responsibilities: Save triage results, manage schema

### 👤 MEMBER 7 — Real-Time Feature ⚡
- Owns: WebSocket system, Live updates
- Works on: realtime/consumers.py, broadcast_service.py
- Responsibilities: Send updates after triage

### 👤 MEMBER 8 — Dashboard API + Integration 🧪
- Owns: Patient list API, End-to-end flow
- Works on: /api/patients/, integration testing
- Responsibilities: Fetch sorted patients, test full system

---

## 🔄 FEATURE FLOW (HOW THEY CONNECT)

```
Login (M1, M2)
   ↓
Submit Symptoms (M3)
   ↓
AI Processing (M4)
   ↓
Validation + Logic (M5)
   ↓
Save Data (M6)
   ↓
WebSocket Broadcast (M7)
   ↓
Dashboard API (M8)
```

---

## ⚖️ FAIRNESS CHECK

| Member | Work Type         | Load   | Status |
|--------|-------------------|--------|--------|
| 1      | Auth core         | Medium | ✅     |
| 2      | Security          | Medium | ✅     |
| 3      | Input feature     | Medium | ✅     |
| 4      | AI                | Medium | ✅     |
| 5      | Logic             | Medium | ✅     |
| 6      | DB                | Medium | ✅     |
| 7      | WebSocket         | Medium | ✅     |
| 8      | API + Testing     | Medium | ✅     |

- ✔ Everyone has equal complexity
- ✔ No one overloaded
- ✔ No idle members

---

## 🤝 CONTROLLED COLLABORATION

- **Auth Group:** Member 1 + Member 2
- **AI Pipeline Group:** Member 4 + Member 5
- **Data Flow Group:** Member 5 + Member 6
- **Real-Time Group:** Member 7 + Member 8

---

## 🧠 WHY THIS IS BETTER (FOR HACKATHON)
- ✔ Parallel development: Everyone can work independently
- ✔ Less blocking: No waiting for other modules
- ✔ Clear ownership: Each feature = one owner
- ✔ Easier debugging: You know exactly who owns what
- ✔ Keeps Django Clean: apps + services respected
- ✔ Keeps Team Fast: parallel development
- ✔ Keeps Features Connected: not isolated like module-based
- ✔ Prevents Chaos: clearer than feature-based only

---

## FINAL HYBRID TEAM DISTRIBUTION (BEST VERSION)

### 🔐 LAYER 1: AUTH & SECURITY (2 MEMBERS)
- Member 1 — Auth Core: Login API, JWT generation, User model
- Member 2 — Authorization & Protection: Role-based access, Permissions, WebSocket auth

### 🌐 LAYER 2: API LAYER (2 MEMBERS)
- Member 3 — Patient APIs: /api/triage/, input validation
- Member 4 — Dashboard APIs: /api/patients/, sorting & response formatting

### 🧠 LAYER 3: SERVICE LAYER (2 MEMBERS)
- Member 5 — AI Service: OpenAI/Gemini, prompt + response
- Member 6 — Triage Logic Service: validation, urgency score, fallback logic

### 🗄️ LAYER 4: DATA LAYER (1 MEMBER + SUPPORT)
- Member 7 — Database Engineer: models, migrations, relationships
- Support: Works with API + Service members

### ⚡ LAYER 5: REAL-TIME SYSTEM (1 MEMBER + SUPPORT)
- Member 8 — WebSocket Engineer: Django Channels, Redis, live updates
- Support: Works with API + Service layer

### 🧪 LAYER 6: INTEGRATION (SHARED)
- Everyone contributes, led by Member 1 (Lead) and Member 8 (Testing)

---

## HOW FEATURES MAP INTO THIS

- **Authentication Feature:** Layer 1 (Member 1, 2)
- **Symptom Submission:** Layer 2 (M3) → Layer 3 (M5, M6) → Layer 4 (M7)
- **AI Triage:** Layer 3 (M5, M6)
- **Dashboard:** Layer 2 (M4) → Layer 4 (M7)
- **Real-Time Updates:** Layer 5 (M8)

---

## ⚖️ FINAL FAIRNESS CHECK

| Member | Layer         | Load   | Status |
|--------|--------------|--------|--------|
| 1      | Auth + Lead  | Medium | ✅     |
| 2      | Auth         | Medium | ✅     |
| 3      | API          | Medium | ✅     |
| 4      | API          | Medium | ✅     |
| 5      | AI           | Medium | ✅     |
| 6      | Logic        | Medium | ✅     |
| 7      | DB           | Medium | ✅     |
| 8      | WebSocket    | Medium | ✅     |

- ✔ Perfect balance
- ✔ No overload
- ✔ No idle

---

## 🧠 WHY THIS IS THE BEST APPROACH
- ✔ Keeps Django Clean (apps + services respected)
- ✔ Keeps Team Fast (parallel development)
- ✔ Keeps Features Connected (not isolated)
- ✔ Prevents Chaos (clearer than feature-based only)

---

# 🏗️ TEAM ASSIGNMENT APPROACHES

## 1. Module-Based Approach
- Each team member owns a Django app/module (e.g., authentication, patients, triage, realtime, dashboard, core).
- Responsibilities are divided by technical boundaries (models, views, serializers, services, tests) within each module.
- Collaboration is required for cross-module features.
- **Pros:** Clear code ownership, easy onboarding for new members.
- **Cons:** Can create bottlenecks if features span multiple modules; less parallelism for feature delivery.

## 2. Feature-Based Approach
- Each member owns a feature slice (e.g., authentication, symptom submission, AI processing, triage logic, data management, real-time, dashboard, integration/testing).
- Responsibilities span across modules (models, services, views, serializers) for their feature.
- Collaboration is required for integration and shared logic.
- **Pros:** Parallel development, clear feature ownership, easier debugging.
- **Cons:** Requires strong communication to avoid code conflicts; onboarding can be more complex.

## 3. Hybrid Approach (Recommended)
- Combines module and feature-based strategies.
- Members are assigned to layers (Auth & Security, API, Service, Data, Real-Time, Integration) and also own features within those layers.
- Collaboration groups are defined for critical flows (Auth, AI, Data, Real-Time, Integration).
- Workload is balanced and responsibilities are clear.
- **Pros:** Maximizes parallelism, clear ownership, balanced workload, and strong collaboration.
- **Cons:** Requires good documentation and coordination.

---

> See detailed breakdowns in the sections above for each approach, including member roles, feature flows, fairness checks, and collaboration groups.

# 📡 📄 API CONTRACT DOCUMENTATION

## 🏥 Project: TriageSync – AI-Powered Real-Time Medical Priority System

### 🧠 1. BASE INFORMATION
- **Base URL:** https://your-domain.com/api/
- **Authentication Type:** JWT (JSON Web Token)
- **Headers (Required for protected routes):**
  ```json
  {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
  }
  ```

### 🔐 2. AUTHENTICATION API
#### 🔑 2.1 LOGIN
- **Endpoint:** POST /api/auth/login/
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "123456"
  }
  ```
- **Response (Success):**
  ```json
  {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "role": "patient"
  }
  ```
- **Response (Failure):**
  ```json
  {
    "error": "Invalid credentials"
  }
  ```

#### 🔄 2.2 REFRESH TOKEN
- **Endpoint:** POST /api/auth/refresh/
- **Request:**
  ```json
  {
    "refresh_token": "token"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "new_access_token"
  }
  ```

### 🧑 3. PATIENT SUBMISSION API
#### 📝 3.1 SUBMIT SYMPTOMS (CORE FEATURE)
- **Endpoint:** POST /api/triage/
- **Access:** Patient only, JWT required
- **Request Body:**
  ```json
  {
    "description": "Chest pain and sweating for 30 minutes"
  }
  ```
- **Validation Rules:**
  - Max length: 500 characters
  - Cannot be empty
- **Response (Success):**
  ```json
  {
    "id": 101,
    "priority": 1,
    "urgency_score": 95,
    "condition": "Cardiac Event",
    "status": "processed",
    "created_at": "2026-04-14T10:30:00Z"
  }
  ```
- **Response (AI Fallback):**
  ```json
  {
    "id": 101,
    "priority": 3,
    "urgency_score": 50,
    "condition": "Unknown - Needs Review",
    "status": "fallback"
  }
  ```

### 📊 4. DASHBOARD API (STAFF ONLY)
#### 📋 4.1 GET ALL PATIENTS
- **Endpoint:** GET /api/patients/
- **Access:** Staff only, JWT required
- **Response:**
  ```json
  [
    {
      "id": 101,
      "description": "Chest pain...",
      "priority": 1,
      "urgency_score": 95,
      "condition": "Cardiac Event",
      "created_at": "2026-04-14T10:30:00Z"
    },
    {
      "id": 102,
      "description": "Headache...",
      "priority": 3,
      "urgency_score": 60,
      "condition": "Migraine"
    }
  ]
  ```
- **Sorting Rule:** Sorted by urgency_score DESC

### 🧠 5. AI TRIAGE INTERNAL PIPELINE (NOT PUBLIC)
- **AI INPUT FORMAT:**
  ```json
  {
    "description": "string"
  }
  ```
- **AI OUTPUT (STRICT FORMAT):**
  ```json
  {
    "priority": 1-5,
    "urgency_score": 0-100,
    "condition": "string"
  }
  ```
- **Rules:**
  - Must return JSON only
  - No explanations
  - No extra text
  - Invalid output triggers fallback system

### ⚡ 6. REAL-TIME WEB SOCKET API
- **Connection:** ws://your-domain.com/ws/triage/
- **Auth (IMPORTANT):**
  - First message after connect:
    ```json
    {
      "token": "jwt_token_here"
    }
    ```
- **Event: NEW PATIENT UPDATE (Server → Client):**
  ```json
  {
    "type": "patient_update",
    "data": {
      "id": 101,
      "priority": 1,
      "urgency_score": 95,
      "condition": "Cardiac Event"
    }
  }
  ```
- **Event Types:**
  | Event           | Description                |
  |-----------------|---------------------------|
  | patient_update  | New patient added         |
  | triage_update   | AI processed result       |
  | system_alert    | Critical patient warning  |

### 🔒 7. ERROR HANDLING STANDARD
- **401 Unauthorized:**
  ```json
  { "error": "Unauthorized access" }
  ```
- **403 Forbidden:**
  ```json
  { "error": "Permission denied" }
  ```
- **400 Validation Error:**
  ```json
  {
    "error": "Invalid input",
    "details": {
      "description": "Cannot exceed 500 characters"
    }
  }
  ```
- **500 Server Error:**
  ```json
  { "error": "Internal server error" }
  ```

### ⚙️ 8. SYSTEM BEHAVIOR RULES
- **Triage Rules:**
  - Priority 1 = Critical (life-threatening)
  - Priority 5 = Low urgency
- **Sorting Rule:** urgency_score DESC
- **Real-time Rule:** Update latency < 1 second; every new triage triggers WebSocket broadcast
- **Data Storage Rule:** Every submission stores description, AI output, timestamp, priority, urgency_score

### 🏗️ 9. FULL END-TO-END FLOW
1. Patient logs in (JWT issued)
2. Patient submits symptoms
3. Backend validates input
4. AI processes symptom
5. Triage engine assigns priority
6. Data stored in DB
7. WebSocket broadcasts update
8. Staff dashboard updates instantly

### 🏆 FINAL NOTES
This API contract ensures:
- ✔ Frontend-backend alignment
- ✔ Clean Django implementation
- ✔ Stable AI integration
- ✔ Safe fallback behavior
- ✔ Real-time update consistency
- ✔ Hackathon-ready demo stability
