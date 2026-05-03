# API Reference

This document provides a comprehensive list of the REST API endpoints available in TriageSync.

## 🏥 Patient Endpoints

### 1. Submit Triage Request
`POST /api/v1/triage/`
- **Body**: `{"description": "string"}`
- **Response**: Full `TriageItem` object (see Schema below).
- **Behavior**: Triggers real-time AI analysis and broadcasts to staff.
- **Note**: This endpoint does not accept or persist new photo uploads. Use the profile endpoints to upload or manage a patient's `profile_photo` and `profile_photo_name`.

### 2. Standalone AI Analysis
`POST /api/v1/triage/ai/`
- **Purpose**: Get a triage recommendation without creating a permanent record.
- **Body**: `{"symptoms": "...", "age": 45, "gender": "male"}`
- **Response**: AI assessment including priority, condition, and reasoning.

### 3. Personal Profile
`GET /api/v1/profile/` | `PATCH /api/v1/profile/`
- **Purpose**: Manage patient demographics and health history.
- **Fields**: `name`, `age`, `gender`, `blood_type`, `health_history`, `allergies`, `medications`, `lifestyle_habits`, `profile_photo` (file), `profile_photo_name` (string).

The profile endpoints accept an optional `profile_photo` file upload and return `profile_photo_name` for display. This is the supported location for new patient photo uploads.

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
`PATCH /api/v1/triage/{id}/assign/`
- **Access**: Staff/Admin only.
- **Behavior**: Assigns the logged-in staff member to the case and moves status to `in_progress`.

### 5. Verify Case
`PATCH /api/v1/dashboard/staff/patient/{id}/verify/`
- **Purpose**: Medical professional sign-off on AI priority.

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

## ⚠️ Error Handling

The API uses standardized error codes for easier frontend handling:

| Code | Status | Meaning |
| :--- | :--- | :--- |
| `VALIDATION_ERROR` | 400 | Missing or invalid fields. |
| `INVALID_CREDENTIALS`| 401 | Login failed. |
| `FORBIDDEN` | 403 | User role does not have permission. |
| `NOT_FOUND` | 404 | Resource does not exist. |
| `TRIAGE_ERROR` | 502 | AI service is temporarily down (Switch to manual). |
