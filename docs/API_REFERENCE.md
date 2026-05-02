# API Reference

This document provides a comprehensive list of the REST API endpoints available in TriageSync.

## 🏥 Patient Endpoints

### 1. Submit Triage Request
`POST /api/v1/triage/`
- **Body**: `{"description": "string", "photo_name": "string"}`
- **Response**: Full `TriageItem` object (see Schema below).
- **Behavior**: Triggers real-time AI analysis and broadcasts to staff.

### 2. Standalone AI Analysis
`POST /api/v1/triage/ai/`
- **Purpose**: Get a triage recommendation without creating a permanent record.
- **Body**: `{"symptoms": "...", "age": 45, "gender": "male"}`
- **Response**: AI assessment including priority, condition, and reasoning.

### 3. Personal Profile
`GET /api/v1/profile/` | `PATCH /api/v1/profile/`
- **Purpose**: Manage patient demographics and health history.
- **Fields**: `name`, `age`, `gender`, `blood_type`, `health_history`, `allergies`, `medications`, `lifestyle_habits`.

---

## 👨‍⚕️ Staff & Clinical Endpoints (Nurse/Doctor/Admin)

### 1. Patient Queue
`GET /api/v1/dashboard/staff/patients/`
- **Filters**: `status` (waiting/in_progress/completed), `priority` (1-5).
- **Ordering**: Automatically sorted by priority (1=Critical) and urgency score.

### 2. Patient Detail (Clinical View)
`GET /api/v1/patients/submissions/{id}/`
- **Access**: Staff/Admin only (unless it's the patient's own record).
- **Returns**: Complete clinical profile and AI diagnostic reasoning.

### 3. Update Status
`PATCH /api/v1/dashboard/staff/patient/{id}/status/`
- **Body**: `{"status": "in_progress"}`
- **Transitions**: `waiting` -> `in_progress` -> `completed`.

### 4. Staff Assignment
`PATCH /api/v1/staff/patient/{id}/assign/`
- **Access**: Staff/Admin only.
- **Behavior**: Assigns the logged-in staff member to the case and moves status to `in_progress`.
- **Also available at**: `PATCH /api/v1/triage/{id}/assign/` (legacy path, both are active)

### 5. Verify Case
`PATCH /api/v1/dashboard/staff/patient/{id}/verify/`
- **Purpose**: Medical professional sign-off on AI priority.
- **Also available at**: `PATCH /api/v1/staff/patient/{id}/verify/`

### 6. Staff Notes
`GET /api/v1/staff/patient/{id}/notes/`
- **Access**: Staff/Admin (all notes). Patients see only non-internal notes on their own submissions.
- **Response**: Array of `StaffNote` objects.

`POST /api/v1/staff/patient/{id}/notes/`
- **Access**: Staff/Admin only.
- **Body**: `{"content": "string", "is_internal": true}`
- **Response**: Created `StaffNote` object.

### 7. Vitals History
`GET /api/v1/staff/patient/{id}/vitals/history/`
- **Access**: Staff/Admin. Patients can view their own.
- **Response**: Array of `VitalsLog` objects ordered by most recent first.

`POST /api/v1/triage/{id}/vitals/`
- **Access**: Staff/Admin only.
- **Body**: `{"blood_pressure": "120/80", "heart_rate": 72, "temperature": 37.1}`

---

## 📋 Data Schema: TriageItem

The `TriageItem` is the core object returned by detail and history endpoints.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Unique identifier. |
| `patient_name` | String | Full name of the patient. |
| `patient_age` | Integer | Patient age at time of submission. |
| `patient_blood_type`| String | A+, O-, etc. (Crucial for hemorrhage cases). |
| `symptoms` | String | Raw text description provided by user. |
| `condition` | String | AI-detected clinical impression. |
| `priority` | Integer | Triage Level (1-5, where 1 is Critical). |
| `urgency_score` | Integer | Granular severity (0-100). |
| `confidence` | Float | AI self-assessed certainty (0.0 - 1.0). |
| `reason` | String | Medically grounded AI reasoning for the level. |
| `explanation` | Array | Specific symptom vectors identified by AI. |
| `status` | String | `waiting`, `in_progress`, or `completed`. |
| `assigned_staff_name`| String | Username of assigned nurse/doctor. |

---

## 🔔 Notification Endpoints

### 1. List Notifications
`GET /api/v1/notifications/`
- **Access**: Authenticated users (own notifications only).
- **Filters**: `is_read=true|false`, `notification_type=<type>`
- **Response**: `{"data": {"count": N, "results": [...]}}`

### 2. Unread Count
`GET /api/v1/notifications/unread-count/`
- **Response**: `{"data": {"unread_count": N}}`

### 3. Mark All Read
`PATCH /api/v1/notifications/read-all/`
- **Response**: `{"data": {"message": "All notifications marked as read", "count": N}}`

### 4. Mark Single Read
`PATCH /api/v1/notifications/{id}/read/`
- **Response**: `{"data": <NotificationObject>}`

---

## 🛡️ Admin Endpoints

### 1. List Users
`GET /api/v1/admin/users/`
- **Access**: Admin only.

### 2. Update User Role
`PATCH /api/v1/admin/users/{id}/role/`
- **Body**: `{"role": "nurse|doctor|admin|patient"}`

### 3. Suspend / Unsuspend User
`PATCH /api/v1/admin/users/{id}/suspend/`
- **Body**: `{"is_suspended": true, "reason": "string"}`

### 4. Delete User
`DELETE /api/v1/admin/users/{id}/`

### 5. Audit Logs
`GET /api/v1/admin/audit-logs/`
- **Access**: Admin only.
- **Response**: Array of `AuditLog` objects ordered by most recent first.
- **Fields**: `id`, `timestamp`, `actor_name`, `action_type`, `target_description`, `justification`, `metadata`

### 6. Report Summary
`GET /api/v1/admin/reports/summary/`
- **Query params**: `start_date`, `end_date` (ISO 8601)

---

## ⚠️ Error Handling

The API uses standardized error codes for easier frontend handling:

| Code | Status | Meaning |
| :--- | :--- | :--- |
| `VALIDATION_ERROR` | 400 | Missing or invalid fields. |
| `INVALID_CREDENTIALS`| 401 | Login failed. |
| `FORBIDDEN` | 403 | User role does not have permission. |
| `NOT_FOUND` | 404 | Resource does not exist. |
| `TRIAGE_ERROR` | 502 | AI service is temporarily down (Switch to manual). |
