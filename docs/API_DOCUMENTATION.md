# TriageSync API Reference

**Version**: 1.5.0  
**Environment**: Development & Production  
**Base URL (Dev)**: `http://localhost:8000/api/v1`  
**Base URL (Prod)**: `https://django-backend-4r5p.onrender.com/api/v1`

---

## 📖 1. Overview

TriageSync provides a robust RESTful API and WebSocket interface for real-time medical triage management. This documentation is designed for frontend developers and system integrators.

### Content Type
All API requests and responses use `application/json` unless otherwise specified (e.g., multipart/form-data for file uploads).

### Standard Response Envelope
Most successful requests return the resource directly (no success envelope). However, some specific endpoints (like Notifications) may wrap data in a `"data"` key.

### Standard Error Response
When an error occurs, the API returns a standardized JSON payload with a `4xx` or `5xx` status code.

```json
{
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable description of the error.",
    "details": {
        "field_name": ["Specific validation error message"]
    }
}
```

---

## 🔒 2. Authentication & Security

### JWT Implementation
TriageSync uses JSON Web Tokens (JWT) for stateless authentication.

1. **Obtain Tokens**: Send credentials to `/auth/login/`.
2. **Authorize Requests**: Include the access token in the `Authorization` header.
   ```http
   Authorization: Bearer <access_token>
   ```
3. **Refresh Tokens**: When the access token expires (60 mins), use the refresh token at `/auth/refresh/` to get a new one.

### User Roles (RBAC)
Endpoints are protected by Role-Based Access Control.

| Role | Scope |
| :--- | :--- |
| `patient` | Access to own medical history, profile, and triage submission. |
| `staff` | Generic staff access: View queue and patient details. |
| `nurse` | Clinical staff: Queue management, vitals logging, priority updates. |
| `doctor` | Medical oversight: Full staff access + Advanced clinical decision making. |
| `admin` | System administration: User management, role assignment, system-wide analytics. |

---

## 🚀 3. Authentication Endpoints

### User Registration
`POST /auth/register/`

Registers a new user. For the `patient` role, demographic fields are mandatory.

**Request Body**:
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "password2": "securepassword123",
    "role": "patient",
    "age": 30,
    "gender": "male",
    "blood_type": "O+",
    "health_history": "None",
    "allergies": "Peanuts",
    "current_medications": "None",
    "bad_habits": "Smoking"
}
```

**Response (201 Created)**:
```json
{
    "access_token": "...",
    "refresh_token": "...",
    "role": "patient",
    "user_id": 1,
    "name": "John Doe",
    "email": "john@example.com"
}
```

### User Login
`POST /auth/login/`

**Request Body**:
```json
{
    "identifier": "john@example.com",
    "password": "securepassword123"
}
```
*Note: The login endpoint is flexible and accepts `identifier`, `email`, or `username` as the key for the user identity. It automatically detects if an email address or username is provided.*

### Token Refresh
`POST /auth/refresh/`

**Request Body**:
```json
{
    "refresh_token": "<your_refresh_token>"
}
```

---

## 👤 4. Profile Management

### Get/Update Profile
`GET /api/v1/profile/` | `PATCH /api/v1/profile/`

A generic endpoint to manage the authenticated user's profile. Mutations return the fully updated profile object.

**Response (Patient)**:
```json
{
    "id": 5,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "patient",
    "age": 30,
    "gender": "male",
    "blood_type": "O+",
    "health_history": "...",
    "allergies": "...",
    "current_medications": "...",
    "bad_habits": "..."
}
```

---

## 🏥 5. Triage Engine

### Submit Triage Request
`POST /triage/`

The primary endpoint for submitting symptoms. Supports AI analysis and image uploads. Returns the created `TriageItem`.

**Request (Multipart Form-Data)**:
- `description` (string, required): Detailed symptoms.
- `photo` (file, optional): Image of injury/condition.
- `blood_type` (string, optional): Overrides profile value for this session.

**Response (201 Created)**:
```json
{
    "id": 12,
    "description": "Severe chest pain and shortness of breath.",
    "priority": 1,
    "urgency_score": 95,
    "condition": "Potential Myocardial Infarction",
    "category": "Cardiac",
    "status": "waiting",
    "is_critical": true,
    "photo_url": "...",
    "explanation": ["High heart rate", "Acute pain"],
    "recommended_action": "Immediate ER admission",
    "confidence": 0.95,
    "source": "ai",
    "created_at": "2024-03-20T10:00:00Z"
}
```

### PDF Symptom Extraction
`POST /triage/pdf-extract/`

Extracts symptoms and demographics from a medical report PDF.

**Request (Multipart Form-Data)**:
- `file` (file, required): PDF document.

### Waiting Analytics
`GET /triage/{id}/waiting-analytics/`

Retrieves real-time queue position and estimated wait time for a specific submission.

**Response**:
```json
{
    "submission_id": 12,
    "minutes_waiting": 5.2,
    "queue_position": 2,
    "patients_ahead": 1,
    "estimated_wait_minutes": 15.0,
    "sla_target_minutes": 5,
    "sla_breach_risk": True
}
```

---

## 📋 6. Patient Portal

### My History
`GET /patients/history/`

Returns a paginated list of the patient's past triage submissions.

**Query Parameters**:
- `page` (int): Page number.
- `page_size` (int): Number of items per page.

### Current Session
`GET /patients/current/`

Retrieves the most recent active (non-completed) triage session.

### Global Triage History
`GET /triage-submissions/`

Accessible by all roles. Patients only see their own records, while staff see all records. Supports filtering by email for staff.

**Query Parameters**:
- `email` (string, optional): Filter by patient email (Staff only).

---

## 🩺 7. Staff Dashboard (Nurses/Doctors)

### Global Queue
`GET /dashboard/staff/patients/`

Operational queue of all active triage cases.

**Query Parameters**:
- `status`: Filter by `waiting`, `in_progress`, or `completed`.
- `priority`: Filter by priority level (1-5).

### Update Patient Status
`PATCH /dashboard/staff/patient/{id}/status/`

Updates the workflow status. Returns the updated `TriageItem` object.

**Request Body**:
```json
{ "status": "in_progress" }
```

### Update Patient Priority
`PATCH /dashboard/staff/patient/{id}/priority/`

Updates the triage priority. Returns the updated `TriageItem` object.

**Request Body**:
```json
{ "priority": 2 }
```

### Verify Patient Identity
`PATCH /dashboard/staff/patient/{id}/verify/`

Marks a patient as verified. Returns the updated `TriageItem` object.

### Log Vitals
`POST /dashboard/staff/patient/{id}/vitals/`

Logs a new set of vitals. Returns the updated `TriageItem` object including the new vitals in the `vitals` array.

**Request Body**:
```json
{
    "temperature_c": 37.5,
    "heart_rate": 88,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "oxygen_saturation": 98,
    "pain_score": 4,
    "notes": "Patient stable."
}
```

---

## 🔔 8. Notifications

### List Notifications
`GET /notifications/`

**Query Parameters**:
- `is_read` (boolean, optional): Filter by read status (`true`/`false`).
- `notification_type` (string, optional): Filter by type (e.g., `critical_alert`).

**Response**:
```json
{
    "data": {
        "count": 1,
        "results": [
            {
                "id": 1,
                "notification_type": "triage_status_change",
                "title": "Status Updated",
                "message": "Your triage status is now In Progress.",
                "is_read": false,
                "created_at": "...",
                "metadata": {}
            }
        ]
    }
}
```

### Unread Count
`GET /notifications/unread-count/`

Returns the number of unread notifications for the user.

### Mark as Read
`PATCH /notifications/{id}/read/`

### Mark All as Read
`PATCH /notifications/read-all/`

### Notification Preferences
`GET /notifications/preferences/` | `PATCH /notifications/preferences/`

Manage opt-in/opt-out settings for different notification types.

---

## ⚡ 9. Real-time Events (WebSockets)

### Connection
`ws://localhost:8000/ws/triage/events/`

**Authentication**:
Connections must be authenticated via JWT. The token should be passed in the `sec-websocket-protocol` header or via cookie if the frontend is on the same domain.

### Inbound Events (Server -> Client)
All events follow a standardized payload structure.

**Base Event Shape**:
```json
{
    "type": "EVENT_TYPE_STRING",
    "timestamp": "2024-03-20T10:05:00.000Z",
    "data": {
        "submission_id": 12,
        "triage_item": { ...full_triage_item_object... },
        "...": "event_specific_fields"
    }
}
```

**Event Types**:
- `TRIAGE_CREATED`: New triage submission received.
- `PRIORITY_UPDATE`: Staff updated a patient's priority.
- `TRIAGE_UPDATED`: Patient status changed (e.g., waiting -> in_progress).
- `CRITICAL_ALERT`: Triggered for any Priority 1 case.

**Example Payload (`TRIAGE_UPDATED`)**:
```json
{
    "type": "TRIAGE_UPDATED",
    "timestamp": "2024-03-20T10:05:00Z",
    "data": {
        "submission_id": 12,
        "new_status": "in_progress",
        "status": "in_progress",
        "triage_item": {
            "id": 12,
            "status": "in_progress",
            "...": "..."
        }
    }
}
```

---

## 🛠️ 10. Admin Console

...
- `GET /dashboard/admin/analytics/`: Get detailed triage analytics.

---

## 📅 11. Future Roadmap (Planned Features)

The following features are currently in the development pipeline and will be available in future releases:

### 11.1 Audit Logs
- `GET /admin/audit-log/`: System-wide audit trail for administrative actions and role changes.

### 11.2 AI Copilot Flow
- `POST /triage/ai-draft/`: Generates a triage draft for staff review before final submission.
- `POST /triage/{id}/confirm/`: Staff confirmation of an AI-drafted triage.

### 11.3 Health Interoperability
- `GET /fhir/Patient/{id}`: FHIR-compliant patient resource export for integration with external hospital systems.
