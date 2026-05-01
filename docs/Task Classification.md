
<div align="center">
  <h1>🚀 FINAL HYBRID TASK DISTRIBUTION (v6)</h1>
  <h3>Real, Balanced, Backend-Only</h3>
</div>

---

<div align="center">
<b>🧠 SYSTEM BREAKDOWN</b><br>
<i>Views (API) → Services (Logic/AI) → Models (DB) → Events → WebSocket</i>
</div>

<details>
<summary><b>Click to expand member responsibilities</b></summary>



---
### 👤 <span style="color:#1976d2">MEMBER 1 — Core Backend & Shared Infrastructure</span> 🔗
**🛠️ Owns:**
  - core/
    - responses.py, exceptions.py, validators.py, utils.py
**🎯 Responsibilities:**
  - Standard API response format
  - Global exception handling
  - Shared validators (length, required fields)
  - Helper utilities used across modules
**➕ Real Work Added:**
  - Integrate API responses across: patients, dashboard, auth
**🤝 Works With:** M3, M4 (API formatting), M5, M6 (service integration), M8 (testing consistency)


---
### 👤 <span style="color:#388e3c">MEMBER 2 — Authentication & Security</span> 🔐
**🛠️ Owns:**
  - authentication/
    - models.py (User), views.py, serializers.py, permissions.py, services/
**🎯 Responsibilities:**
  - JWT login & refresh
  - Role system (patient/staff/admin)
  - Permission classes
  - WebSocket authentication middleware
**➕ Real Work:**
  - Protect ALL endpoints
  - Role-based access enforcement
**🤝 Works With:** M3, M4 (API protection), M7 (User model relations), M8 (WS auth testing)


---
### 👤 <span style="color:#fbc02d">MEMBER 3 — Patient API (Input Layer)</span> 🧑
**🛠️ Owns:**
  - patients/
    - views.py, serializers.py
**🎯 Responsibilities:**
  - POST /api/triage/
  - Input validation (≤500 chars)
  - Start processing pipeline
  - Emit “new patient” event
**➕ Real Work:**
  - Optional: patient history API
**🤝 Works With:** M5 (AI call), M6 (logic), M7 (DB), M8 (event trigger)

dashboard/

---

### 👤 <span style="color:#7b1fa2">MEMBER 4 — Dashboard APIs (Output Layer)</span> 📊
**🛠️ Owns:**
  - dashboard/
    - views.py, serializers.py
**🎯 Responsibilities:**
  - Staff: patient queue, filtering, sorting
    - Implements and maintains staff endpoints:
      - GET /dashboard/staff/queue/ (mock/placeholder)
      - GET /dashboard/staff/patient/{session_id}/ (mock/placeholder)
      - POST /dashboard/staff/patient/{session_id}/override/ (mock/placeholder)
  - Admin: overview stats, analytics
**➕ Real Work:**
  - Aggregation queries (counts, averages)
  - Ensure staff endpoints are available for frontend integration (currently mock/placeholder responses for demo/testing)
**🤝 Works With:** M6 (logic data), M7 (queries), M2 (permissions), M8 (real-time updates)


---
### 👤 <span style="color:#0288d1">MEMBER 5 — AI Service Layer</span> 🧠
**🛠️ Owns:**
  - triage/services/
    - ai_service.py, prompt_engine.py
**🎯 Responsibilities:**
  - Call OpenAI/Gemini
  - Build prompts
  - Parse response
**➕ Real Work:**
  - Retry mechanism
  - Timeout handling
**🤝 Works With:** M3 (input), M6 (logic), M1 (integration)


---
### 👤 <span style="color:#c62828">MEMBER 6 — Triage Logic & Business Rules</span> ⚙️
**🛠️ Owns:**
  - triage/services/
    - triage_service.py, validation_service.py
**🎯 Responsibilities:**
  - urgency score
  - priority mapping
  - fallback system
  - status transitions
**➕ Real Work:**
  - critical alert logic
  - event triggers
**🤝 Works With:** M5 (AI output), M7 (DB), M4 (dashboard), M8 (events)


---
### 👤 <span style="color:#6d4c41">MEMBER 7 — Data Layer (Models & Queries)</span> 🗄️
**🛠️ Owns:**
  - patients/models.py, triage/models.py, authentication/models.py
**🎯 Responsibilities:**
  - All models, relationships, migrations, optimized queries
**➕ Real Work:**
  - Admin APIs (user + patient management)
**🤝 Works With:** M3 (store input), M6 (store results), M4 (fetch data), M2 (roles)


---
### 👤 <span style="color:#f57c00">MEMBER 8 — Real-Time System & Backend Testing</span> ⚡🧪
**🛠️ Owns:**
  - realtime/
    - consumers.py, routing.py, services/broadcast_service.py
**🎯 Responsibilities:**
  - Django Channels, Redis, WebSocket broadcasting
  - Backend testing (Postman, scripts)
**➕ Real Work:**
  - Performance testing
  - Integration testing
**🤝 Works With:** M3 (submission event), M6 (logic events), M4 (payload structure), M2 (security), M1 (integration)

</details>

---
<div align="center">
<b>⚡ REAL-TIME DISTRIBUTION (FINAL FIXED)</b>
</div>

| Task                | Owner |
|---------------------|-------|
| WebSocket setup     | M8    |
| Redis config        | M8    |
| Submission trigger  | M3    |
| Logic trigger       | M6    |
| Payload format      | M4    |
| Security            | M2    |
| Integration/debug   | M1    |

<div align="center">
👉 ✔ <b>Shared properly</b> &nbsp;&nbsp; 👉 ✔ <b>No overload</b>
</div>

---

<div align="center">
<b>🔄 FINAL SYSTEM FLOW (LOCKED)</b>
</div>

1. <b>POST /api/triage/</b>       → <b>M3</b>
2. <b>AI processing</b>           → <b>M5</b>
3. <b>Triage logic</b>            → <b>M6</b>
4. <b>Save to DB</b>              → <b>M7</b>
5. <b>Emit event</b>              → <b>M3/M6</b>
6. <b>WebSocket broadcast</b>     → <b>M8</b>
7. <b>Dashboard API fetch</b>     → <b>M4</b>

---
---
