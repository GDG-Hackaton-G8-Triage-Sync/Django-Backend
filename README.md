# Django-Backend
# 📊 Dashboard API (Member 4 – Output Layer)

## 🚀 Overview

This module implements the **Dashboard APIs** for the TriageSync system.

Its purpose is to expose **processed triage data** (not raw input) in a way that healthcare staff and admins can quickly make decisions.

👉 It does **NOT** handle:

* Patient submission (handled by Patient API)
* AI processing (handled by AI/Triage services)

👉 It **DOES** handle:

* Patient queue (sorted by urgency)
* Filtering and workflow updates
* Admin system statistics and analytics

---

## 🧠 Architecture

```
Views → Services → Models → Response
```

* **Views**: Handle HTTP requests
* **Services**: Business logic (filtering, aggregation)
* **Models**: PatientSubmission (data source)
* **Serializers**: Format output to match API contract

---

## 📦 Endpoints Implemented

### 👩‍⚕️ 1. Staff Dashboard

#### 🔹 Get Patient Queue

```
GET /api/dashboard/staff/patients/
```

Returns:

* All patients sorted by `urgency_score DESC`

Example:

```json
[
  {
    "id": 1,
    "description": "Chest pain",
    "priority": 1,
    "urgency_score": 95,
    "condition": "Cardiac Event",
    "status": "waiting",
    "created_at": "2026-04-14T10:30:00Z"
  }
]
```

---

#### 🔹 Filter Patients

```
GET /api/dashboard/staff/patients/?priority=1
GET /api/dashboard/staff/patients/?status=waiting
```

---

#### 🔹 Update Patient Status

```
PATCH /api/dashboard/staff/patient/{id}/status/
```

Request:

```json
{
  "status": "in_progress"
}
```

---

### 🛠️ 2. Admin Dashboard

#### 🔹 System Overview

```
GET /api/dashboard/admin/overview/
```

Response:

```json
{
  "total_patients": 120,
  "waiting": 45,
  "in_progress": 30,
  "completed": 45,
  "critical_cases": 10
}
```

---

#### 🔹 Analytics (Optional)

```
GET /api/dashboard/admin/analytics/
```

Response:

```json
{
  "avg_urgency_score": 67,
  "common_conditions": [
    { "condition": "Cardiac Event", "count": 10 }
  ]
}
```

---

## 🧩 Key Implementation Details

### 1. Serializer

* Renames `symptoms` → `description` to match API contract
* Exposes only required fields

---

### 2. Service Layer

* Handles:

  * Filtering (priority, status)
  * Sorting (urgency_score DESC)
  * Aggregations (counts, averages)

👉 Keeps views clean and maintainable

---

### 3. Sorting Logic

Patients are always sorted by:

```
urgency_score DESC
```

👉 Critical patients appear first

---

### 4. Workflow Status

Supported values:

* `waiting`
* `in_progress`
* `completed`

---

## 🧪 How to Test (Postman)

### 1. Login

```
POST /api/auth/login/
```

Copy:

```
access_token
```

---

### 2. Add Authorization Header

```
Authorization: Bearer <token>
```

---

### 3. Test Endpoints

#### Get Patients

```
GET /api/dashboard/staff/patients/
```

#### Filter

```
GET /api/dashboard/staff/patients/?status=waiting
```

#### Update Status

```
PATCH /api/dashboard/staff/patient/1/status/
```

Body:

```json
{
  "status": "in_progress"
}
```

#### Admin Overview

```
GET /api/dashboard/admin/overview/
```

---

## ⚠️ Dependencies

This module depends on:

### 🔗 Member 6 (Triage Logic)

* Provides:

  * priority
  * urgency_score
  * condition

---

### 🔗 Member 7 (Models)

* Fields required in `PatientSubmission`:

  * priority
  * urgency_score
  * condition
  * status

---

### 🔗 Member 2 (Authentication)

* Required for:

  * role-based access (staff/admin)

---

### 🔗 Member 8 (Real-Time)

* Dashboard data used for WebSocket updates

---

## 🚫 Limitations (Current State)

* No real-time updates yet
* No permission enforcement yet
* AI scoring may still be basic
* Depends on complete triage pipeline

---

## 🧠 Design Decisions

* Used **service layer** instead of putting logic in views
* Used **DB-level sorting** for performance
* Avoided mixing responsibilities with other modules
* Followed API contract strictly

---

## ✅ Status

✔ Staff dashboard API complete
✔ Admin overview implemented
✔ Filtering and sorting working
✔ Ready for integration with triage + real-time system

---

## 📌 Next Steps

* Integrate with real-time updates (WebSocket)
* Add role-based permissions
* Connect full pipeline (triage → DB → dashboard)
