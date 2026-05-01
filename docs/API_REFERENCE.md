# API Reference

This document provides a comprehensive list of the REST API endpoints available in TriageSync.

## 🏥 Patient Endpoints

### 1. Submit Triage Request
`POST /api/v1/triage/`
- **Body**: `{"description": "string", "photo_name": "string"}`
- **Note**: Triggers real-time AI analysis and broadcasts to staff.

### 2. Standalone AI Analysis
`POST /api/v1/triage/ai/`
- **Purpose**: Get a triage recommendation without creating a permanent record.
- **Body**: `{"symptoms": "...", "age": 45, "gender": "male"}`

### 3. Personal Profile
`GET /api/v1/profile/` | `PATCH /api/v1/profile/`
- **Purpose**: Manage patient demographics and health history (allergies, medications).

---

## 👨‍⚕️ Staff & Clinical Endpoints (Nurse/Doctor)

### 1. Patient Queue
`GET /api/v1/dashboard/staff/patients/`
- **Filters**: `status` (waiting/in_progress/completed), `priority` (1-5).
- **Ordering**: Automatically sorted by priority (1=Critical) and urgency score.

### 2. Update Status
`PATCH /api/v1/dashboard/staff/patient/{id}/status/`
- **Body**: `{"status": "in_progress"}`

### 3. Manual Priority Override
`PATCH /api/v1/dashboard/staff/patient/{id}/priority/`
- **Body**: `{"priority": 1}`

### 4. Verify Case
`PATCH /api/v1/dashboard/staff/patient/{id}/verify/`
- **Purpose**: Mark a case as clinically reviewed.

---

## 🛡️ Admin Endpoints

### 1. User Management
- `GET /api/v1/admin/users/`: List all users.
- `PATCH /api/v1/admin/users/{id}/role/`: Change user roles.
- `PATCH /api/v1/admin/users/{id}/suspend/`: Suspend/Unsuspend accounts.

### 2. System Monitoring
- `GET /api/v1/admin/overview/`: Real-time system stats.
- `GET /api/v1/admin/analytics/`: Trends, peak hours, and condition breakdowns.

---

## ⚠️ Error Handling

The API uses standardized error codes for easier frontend handling:

| Code | Status | Meaning |
| :--- | :--- | :--- |
| `VALIDATION_ERROR` | 400 | Missing or invalid fields. |
| `INVALID_CREDENTIALS`| 401 | Login failed. |
| `FORBIDDEN` | 403 | User role does not have permission. |
| `NOT_FOUND` | 404 | Resource does not exist. |
| `TRIAGE_ERROR` | 502 | AI service is temporarily down. |
