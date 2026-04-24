
# 📡 🔥 UPDATED API CONTRACT (WITH STAFF + ADMIN DASHBOARD)

## 👥 USER ROLES (FINAL)
| Role    | Description                |
|---------|----------------------------|
| patient | submits symptoms           |
| staff   | views real-time queue      |
| admin   | manages system + monitoring|

## 🔐 ROLE RULES
| Endpoint           | Patient | Staff | Admin |
|--------------------|:-------:|:-----:|:-----:|
| Submit symptoms    |   ✅    |  ❌   |  ❌   |
| View dashboard     |   ❌    |  ✅   |  ✅   |
| Admin controls     |   ❌    |  ❌   |  ✅   |

---

## 📊 1. STAFF DASHBOARD API (Flutter Integration)

This is the main UI for healthcare staff


### 📋 1.1 GET STAFF QUEUE (MOCK)
**GET** /api/dashboard/staff/queue/
**Access:** Staff only
**Response:**
```
{
  "total": 2,
  "queue": [
    {
      "session_id": "TS-1111",
      "priority_level": 1,
      "urgency_score": 98,
      "wait_time_seconds": 240
    },
    {
      "session_id": "TS-2222",
      "priority_level": 2,
      "urgency_score": 85,
      "wait_time_seconds": 600
    }
  ]
}
```
**Behavior:**
- Placeholder/mock data for demo

### 🔍 1.2 FILTER PATIENTS (OPTIONAL BUT USEFUL)
**GET** /api/dashboard/staff/patients/?priority=1
or
**GET** /api/dashboard/staff/patients/?status=waiting


### 1.2 GET PATIENT DETAIL (MOCK)
**GET** /api/dashboard/staff/patient/{session_id}/
**Response:**
```
{
  "session_id": "TS-1111",
  "symptoms": "Chest pain...",
  "vitals": {
    "hr": 110,
    "spo2": 92
  },
  "ai_reasoning": {
    "condition": "ACS"
  }
}
```
**Behavior:**
- Placeholder/mock data for demo

### 1.3 OVERRIDE PRIORITY (MOCK)
**POST** /api/dashboard/staff/patient/{session_id}/override/
**Request:**
```
{
  "new_priority": 2,
  "reason": "Clinical observation"
}
```
**Response:**
```
{
  "success": true
}
```
**Behavior:**
- Placeholder/mock data for demo

## ⚡ STAFF REAL-TIME EVENTS (Flutter WebSocket)
**EVENT: NEW PATIENT**
{
  "type": "patient_created",
  "data": {
    "id": 101,
    "priority": 1,
    "urgency_score": 95
  }
}
**EVENT: PRIORITY UPDATE**
{
  "type": "priority_update",
  "data": {
    "id": 101,
    "priority": 1,
    "urgency_score": 98
  }
}
**EVENT: CRITICAL ALERT 🚨**
{
  "type": "critical_alert",
  "message": "Critical patient detected!",
  "data": {
    "id": 101,
    "priority": 1
  }
}

## 🛠️ 2. ADMIN DASHBOARD API (SYSTEM CONTROL)

This is NOT for demo UI only, but adds serious value.

### 📊 2.1 SYSTEM OVERVIEW
**GET** /api/dashboard/admin/overview/
**Response:**
{
  "total_patients": 120,
  "waiting": 45,
  "in_progress": 30,
  "completed": 45,
  "critical_cases": 10
}

### 📈 2.2 GET ANALYTICS (OPTIONAL)
**GET** /api/dashboard/admin/analytics/
**Response:**
{
  "avg_urgency_score": 67,
  "peak_hour": "14:00",
  "common_conditions": ["Cardiac Event", "Migraine"]
}

### 👥 2.3 MANAGE USERS
Get users: **GET** /api/admin/users/
Change role: **PATCH** /api/admin/users/{id}/role/
{
  "role": "staff"
}

### 🚫 2.4 DELETE PATIENT (ADMIN CONTROL)
**DELETE** /api/admin/patient/{id}/

## 📡 3. FLUTTER INTEGRATION GUIDE
### 📱 STAFF APP SCREENS
1. Login Screen → /api/auth/login/
2. Dashboard Screen → /api/dashboard/staff/patients/
   - WebSocket: ws://server/ws/triage/
3. Status Update Button → PATCH /status/

### 📱 ADMIN APP SCREENS
1. Admin Dashboard → /api/dashboard/admin/overview/
2. Analytics Page → /analytics/
3. User Management → /admin/users/

## ⚙️ 4. IMPORTANT BACKEND RULES
### 🔐 Role Enforcement (VERY IMPORTANT)
- Staff endpoints → IsStaff
- Admin endpoints → IsAdmin
- Patient endpoints → IsPatient
### ⚡ Real-Time Trigger Points
WebSocket MUST trigger on:
- new patient created
- triage completed
- priority updated
- status changed
### 🧠 Critical Case Rule
if priority == 1 → trigger critical_alert

## 1. Base Information
- **Base URL:** https://your-domain.com/api/
- **Authentication Type:** JWT (JSON Web Token)
- **Headers (Required for protected routes):**
  ```json
  {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
  }
  ```

## 2. Authentication API
### 2.1 Login
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

### 2.2 Refresh Token
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

## 3. Patient Submission API
### 3.1 Submit Symptoms
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

## 4. Dashboard API
### 4.1 Get All Patients
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
- **Sorting Rule:** urgency_score DESC

## 5. AI Triage Internal Pipeline
- **AI Input Format:**
  ```json
  {
    "description": "string"
  }
  ```
- **AI Output (Strict Format):**
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

## 6. Real-Time WebSocket API (✅ Implemented — Member 8)

- **Connection:** `ws://your-domain.com/ws/triage/events/`
- **Protocol:** Server-push only. Clients connect and listen — do not send messages.
- **Auth:** JWT middleware handled by M2 (plugs into connect phase)

### Event Structure (all events follow this format)
```json
{
  "type": "event_type_here",
  "data": { ... },
  "timestamp": "2026-04-24T10:30:00Z"
}
```

### Event: patient_created
Fires when a new patient is triaged. If priority == 1, `critical_alert` also fires automatically.
```json
{
  "type": "patient_created",
  "data": { "id": 101, "priority": 2, "urgency_score": 75 },
  "timestamp": "2026-04-24T10:30:00Z"
}
```

### Event: priority_update
Fires when triage logic re-evaluates a patient's priority.
```json
{
  "type": "priority_update",
  "data": { "id": 101, "priority": 1, "urgency_score": 92 },
  "timestamp": "2026-04-24T10:31:00Z"
}
```

### Event: critical_alert 🚨
Auto-fires whenever priority == 1 (urgency_score >= 80). Always comes after `patient_created` or `priority_update`.
```json
{
  "type": "critical_alert",
  "data": { "id": 101, "priority": 1, "message": "Critical patient detected!" },
  "timestamp": "2026-04-24T10:31:00Z"
}
```

### Event: status_changed
Fires when staff updates a patient's status.
```json
{
  "type": "status_changed",
  "data": { "id": 101, "status": "in_progress" },
  "timestamp": "2026-04-24T10:32:00Z"
}
```

### Status Values
| Value | Meaning |
|---|---|
| `waiting` | Patient submitted, not yet seen |
| `in_progress` | Staff is attending |
| `completed` | Case resolved |

### Trigger Points (when broadcasts fire)
| Trigger | Event Sent |
|---|---|
| New patient triaged | `patient_created` (+ `critical_alert` if priority 1) |
| Priority re-evaluated | `priority_update` (+ `critical_alert` if priority 1) |
| Staff updates status | `status_changed` |

### Functions other members call (import from broadcast_service)
```python
from apps.realtime.services.broadcast_service import (
    broadcast_patient_created,   # M3 calls after saving submission
    broadcast_priority_update,   # M6 calls after re-evaluation
    broadcast_status_changed,    # M4 calls after status PATCH
)
```

## 7. Error Handling Standard
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

## 8. System Behavior Rules
- **Triage Rules:**
  - Priority 1 = Critical (life-threatening)
  - Priority 5 = Low urgency
- **Sorting Rule:** urgency_score DESC
- **Real-time Rule:** Update latency < 1 second; every new triage triggers WebSocket broadcast
- **Data Storage Rule:** Every submission stores description, AI output, timestamp, priority, urgency_score

## 9. End-to-End Flow
1. Patient logs in (JWT issued)
2. Patient submits symptoms
3. Backend validates input
4. AI processes symptom
5. Triage engine assigns priority
6. Data stored in DB
7. WebSocket broadcasts update
8. Staff dashboard updates instantly

---
This API contract ensures frontend-backend alignment, clean Django implementation, stable AI integration, safe fallback behavior, real-time update consistency, and hackathon-ready demo stability.
