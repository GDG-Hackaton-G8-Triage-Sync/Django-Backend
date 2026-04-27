# 🏥 TriageSync - Member 6 (Triage Logic Service)

## 📌 Overview
This module is responsible for the **core triage decision engine** of the TriageSync system.  
It processes patient symptoms and generates urgency-based medical priorities.

---

## ⚙️ Features Implemented

### 1. Symptom Validation
- Ensures input symptoms are clean and valid before processing.

### 2. AI-Based Priority Inference
- Uses AI service to generate a base urgency score.

### 3. Urgency Scoring System
- Converts symptoms into a numerical urgency score (0–100).

### 4. Priority Mapping
- Score is mapped into priority levels:
  - CRITICAL (80–100)
  - URGENT (60–79)
  - MEDIUM (40–59)
  - STABLE (0–39)

### 5. Status Transitions
- Tracks patient state:
  - PENDING → TRIAGED → ESCALATED → STABLE

### 6. Emergency Override System
- Detects life-threatening keywords (e.g., chest pain, unconscious)
- Immediately escalates to CRITICAL status.

### 7. Event Trigger System
- Generates system events based on triage result:
  - EMERGENCY_ALERT
  - URGENT_ALERT
  - LOG_ONLY

---

## 🔁 Workflow

1. Input symptoms
2. Validate input
3. AI generates urgency score
4. Apply business rules
5. Update status
6. Trigger event
7. Return structured response

---

## 🧪 Test Cases
_See full breakdown in the project documentation or below for member responsibilities, collaboration flows, and fairness checks._


---
<div align="center">
  <h2 style="color:#1976d2; background:#e3f2fd; padding:10px; border-radius:8px;">🔷 MODULE-BASED TEAM ASSIGNMENT</h2>
</div>
---
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



---
<div align="center">
  <h2 style="color:#388e3c; background:#e8f5e9; padding:10px; border-radius:8px;">🟢 FEATURE-BASED TEAM ASSIGNMENT</h2>
</div>
---
# 🧑‍💻 TEAM ASSIGNMENT: SEPARATE FEATURE-BASED APPROACH

Example inputs:
- "Severe chest pain and difficulty breathing"
- "High fever and vomiting"
- "Mild headache"
- "Patient is unconscious"
- "Feeling dizzy and tired"

---

## 📦 Output Format

```json
{
  "success": true,
  "data": {
    "triage_result": {},
    "event": {},
    "source": "AI_SYSTEM | EMERGENCY_OVERRIDE",
    "module": "member6_triage_service"
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

---
<div align="center">
  <h2 style="color:#f57c00; background:#fff3e0; padding:10px; border-radius:8px;">🟠 HYBRID TEAM ASSIGNMENT (BEST VERSION)</h2>
</div>
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

---

<div align="center">
  <h2 style="color:#1976d2; background:#e3f2fd; padding:10px; border-radius:8px;">🔷 1. MODULE-BASED APPROACH</h2>
</div>
---
## 1. Module-Based Approach
- Each team member owns a Django app/module (e.g., authentication, patients, triage, realtime, dashboard, core).
- Responsibilities are divided by technical boundaries (models, views, serializers, services, tests) within each module.
- Collaboration is required for cross-module features.
- **Pros:** Clear code ownership, easy onboarding for new members.
- **Cons:** Can create bottlenecks if features span multiple modules; less parallelism for feature delivery.

---

<div align="center">
  <h2 style="color:#388e3c; background:#e8f5e9; padding:10px; border-radius:8px;">🟢 2. FEATURE-BASED APPROACH</h2>
</div>
---
## 2. Feature-Based Approach
- Each member owns a feature slice (e.g., authentication, symptom submission, AI processing, triage logic, data management, real-time, dashboard, integration/testing).
- Responsibilities span across modules (models, services, views, serializers) for their feature.
- Collaboration is required for integration and shared logic.
- **Pros:** Parallel development, clear feature ownership, easier debugging.
- **Cons:** Requires strong communication to avoid code conflicts; onboarding can be more complex.

---

<div align="center">
  <h2 style="color:#f57c00; background:#fff3e0; padding:10px; border-radius:8px;">🟠 3. HYBRID APPROACH (RECOMMENDED)</h2>
</div>
---
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
}

## 🔗 AI Bridge Layer 

This module acts as a **bridge between AI service and system layers**.

### Responsibilities:
- Receives AI-generated urgency score
- Converts AI output into system-readable format
- Applies business triage rules
- Formats output for:
  - 👩‍⚕️ Staff dashboard
  - 🧑‍💼 Admin dashboard
  - 📦 Database storage
  - ⚡ Event system

### Architecture Flow:

AI Service → AI Bridge (Member 6) → Business Rules → System Output
