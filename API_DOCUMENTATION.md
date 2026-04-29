# TriageSync API Documentation

**Version**: 1.0.0  
**Last Updated**: April 29, 2026  
**Base URL (Development)**: `http://localhost:8000`  
**Base URL (Production)**: `https://django-backend-4r5p.onrender.com`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Authentication Endpoints](#authentication-endpoints)
3. [Triage Endpoints](#triage-endpoints)
4. [Patient Endpoints](#patient-endpoints)
5. [Dashboard Endpoints (Staff Only)](#dashboard-endpoints-staff-only)
6. [Admin Endpoints (Staff Only)](#admin-endpoints-staff-only)
7. [WebSocket Events](#websocket-events)
8. [Error Handling](#error-handling)
9. [Rate Limiting & Pagination](#rate-limiting--pagination)
10. [Status Codes](#status-codes)

---

## Authentication

TriageSync uses **JWT (JSON Web Token)** authentication. Most endpoints require a valid access token in the Authorization header.

### Token Format

```
Authorization: Bearer <access_token>
```

### Token Lifecycle

- **Access Token**: Valid for 60 minutes
- **Refresh Token**: Valid for 7 days
- **Token Refresh**: Use `/api/v1/auth/refresh/` to get a new access token

### User Roles

| Role | Description | Access Level |
|------|-------------|--------------|
| `patient` | End users submitting triage requests | Patient endpoints only |
| `nurse` | Medical staff managing patient queue | Staff + Admin endpoints |
| `doctor` | Medical staff with full access | Staff + Admin endpoints |
| `admin` | System administrators | All endpoints |

---

## Authentication Endpoints

### 1. Register User

Create a new user account.

**Endpoint**: `POST /api/v1/auth/register/`  
**Authentication**: None  
**Permissions**: Public

#### Request Body

```json
{
  "name": "john doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "role": "patient",
  "gender": "male",
  "age": 36,
  "blood_type": "O+",
  "health_history": "No chronic conditions",
  "allergies": "penicillin",
  "current_medications": "none",
  "bad_habits": "smoking"
}
```

> **Note:** For patient registration the following fields must be present: `name`, `email`, `password`, `role`, and `age`. Other patient profile fields (`gender`, `blood_type`, `health_history`, `allergies`, `current_medications`, `bad_habits`) are optional but may be provided at registration and will be saved to the patient profile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Patient full name (mapped to username) |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Password (min 8 chars) |
| `role` | string | Yes | One of: `patient`, `nurse`, `doctor`, `admin` |
| `age` | integer | Yes | Age in years |
| `gender` | string | No | Patient gender (optional) |
| `blood_type` | string | No | Blood type (optional) |
| `health_history` | string | No | Free-text health history (optional) |
| `allergies` | string | No | Known allergies (optional) |
| `current_medications` | string | No | Current medications (optional) |
| `bad_habits` | string | No | Smoking, alcohol etc. (optional) |

#### Success Response (201 Created)

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "role": "patient",
  "user_id": 1,
  "name": "john_doe",
  "email": "john@example.com"
}
```

#### Error Response (400 Bad Request)

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid registration data",
  "details": {
    "username": ["This field is required."],
    "email": ["Enter a valid email address."]
  }
}
```

---

### 2. Login

Authenticate and receive JWT tokens.

**Endpoint**: `POST /api/v1/auth/login/`  
**Authentication**: None  
**Permissions**: Public

#### Request Body

```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

#### Success Response (200 OK)

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "role": "patient",
  "user_id": 1,
  "name": "john_doe",
  "email": "john@example.com"
}
```

#### Error Response (401 Unauthorized)

```json
{
  "code": "AUTHENTICATION_FAILED",
  "message": "Invalid username or password"
}
```

---

### 3. Refresh Token

Get a new access token using refresh token.

**Endpoint**: `POST /api/v1/auth/refresh/`  
**Authentication**: None  
**Permissions**: Public

#### Request Body

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Success Response (200 OK)

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Error Response (401 Unauthorized)

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 4. Get User Profile

Retrieve authenticated user's profile.

**Endpoint**: `GET /api/v1/profile/`  
**Authentication**: Required  
**Permissions**: All authenticated users

#### Request Headers

```
Authorization: Bearer <access_token>
```

#### Success Response - Patient (200 OK)

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "patient",
  "date_of_birth": "1990-05-15",
  "contact_info": "+1234567890",
  "gender": "male",
  "age": 36,
  "blood_type": "O+",
  "health_history": "No major illnesses",
  "allergies": "Penicillin",
  "current_medications": "None",
  "bad_habits": "None"
}
```

#### Success Response - Staff (200 OK)

```json
{
  "id": 2,
  "name": "Dr. Smith",
  "email": "smith@hospital.com",
  "role": "staff",
  "username": "dr_smith"
}
```

---

### 5. Update User Profile

Update authenticated user's profile.

**Endpoint**: `PATCH /api/v1/profile/`  
**Authentication**: Required  
**Permissions**: All authenticated users

#### Request Body - Patient

```json
{
  "name": "John Doe Updated",
  "gender": "male",
  "age": 36,
  "blood_type": "O+",
  "health_history": "Updated history",
  "allergies": "Penicillin, Peanuts",
  "current_medications": "Aspirin 100mg daily",
  "bad_habits": "Smoking"
}
```

#### Request Body - Staff

```json
{
  "name": "Dr. Smith Updated",
  "email": "smith_new@hospital.com"
}
```

#### Success Response (200 OK)

Returns updated profile (same structure as GET /api/v1/profile/)

---

## Triage Endpoints

### 6. Submit Triage Request

Submit a new triage request (main endpoint).

**Endpoint**: `POST /api/v1/triage/`  
**Authentication**: Required  
**Permissions**: Patient role only

#### Request Body

```json
{
  "description": "Severe chest pain radiating to left arm, shortness of breath",
  "photo_name": "chest_xray_001.jpg"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Symptom description (max 500 chars) |
| `photo_name` | string | No | Optional photo filename |

#### Success Response (201 Created)

```json
{
  "id": 123,
  "description": "Severe chest pain radiating to left arm, shortness of breath",
  "priority": 1,
  "urgency_score": 95,
  "condition": "Acute Cardiac Event",
  "status": "waiting",
  "photo_name": "chest_xray_001.jpg",
  "created_at": "2026-04-29T08:00:00.000000Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique submission ID |
| `description` | string | Symptom description |
| `priority` | integer | Priority level (1-5, 1=critical) |
| `urgency_score` | integer | Urgency score (0-100) |
| `condition` | string | Diagnosed condition |
| `status` | string | One of: `waiting`, `in_progress`, `completed` |
| `photo_name` | string | Photo filename (if provided) |
| `created_at` | string | ISO 8601 timestamp |

#### Error Responses

**400 Bad Request - Missing Description**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Description is required"
}
```

**400 Bad Request - Description Too Long**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Description must be 500 characters or less"
}
```

**502 Bad Gateway - Triage Service Error**
```json
{
  "code": "TRIAGE_ERROR",
  "message": "Triage evaluation failed. Please try again later."
}
```

---

### 7. AI Triage Analysis (Standalone)

Get AI triage analysis without creating a submission.

**Endpoint**: `POST /api/v1/triage/ai/`  
**Authentication**: None  
**Permissions**: Public


#### Request Body

```json
{
  "symptoms": "Chest pain and shortness of breath",
  "age": 45,   // Optional if authenticated
  "gender": "male" // Optional if authenticated
}
```

> **Note:** If the user is authenticated, the system will automatically use the patient's saved age and gender from their profile. If unauthenticated, you may provide `age` and `gender` in the request body.

#### Success Response (200 OK)

```json
{
  "priority_level": 1,
  "urgency_score": 95,
  "condition": "Acute Cardiac Event",
  "category": "Cardiac",
  "is_critical": true,
  "explanation": [
    "Chest pain is a critical symptom",
    "Shortness of breath indicates respiratory distress",
    "Combination suggests cardiac emergency"
  ],
  "recommended_action": "Immediate emergency room visit",
  "reason": "Life-threatening cardiac symptoms require immediate medical attention",
  "source": "ai"
}
```

#### Error Response (503 Service Unavailable)

```json
{
  "error": "AI unavailable, staff review required",
  "message": "Our AI triage service is temporarily unavailable. Your case will be queued for staff review.",
  "details": ["All AI models failed", "Circuit breaker open"],
  "error_types": ["MODEL_FAILURE", "CIRCUIT_OPEN"]
}
```

---

### 8. PDF Symptom Extraction

Extract symptoms from PDF medical documents.

**Endpoint**: `POST /api/v1/triage/pdf-extract/`  
**Authentication**: None  
**Permissions**: Public

#### Request Body (multipart/form-data)

```
file: <PDF file> (max 5MB)
age: 45 (optional)
gender: male (optional)
```

#### Success Response (200 OK)

```json
{
  "priority_level": 2,
  "urgency_score": 75,
  "condition": "Respiratory Infection",
  "category": "Respiratory",
  "is_critical": false,
  "explanation": [
    "Persistent cough for 5 days",
    "Fever of 101°F",
    "Mild shortness of breath"
  ],
  "recommended_action": "Visit urgent care within 24 hours",
  "reason": "Symptoms suggest bacterial respiratory infection requiring antibiotics",
  "source": "ai"
}
```

#### Error Responses

**400 Bad Request - Invalid File**
```json
{
  "error": "Only PDF files are allowed.",
  "message": "Please upload a file with a .pdf extension."
}
```

**400 Bad Request - No Text Extracted**
```json
{
  "error": "No text extracted.",
  "message": "No extractable text found in the PDF. Please upload a PDF with selectable text."
}
```

---

## Patient Endpoints

### 9. Get Patient Profile

Get authenticated patient's profile.

**Endpoint**: `GET /api/v1/patients/profile/`  
**Authentication**: Required  
**Permissions**: Patient role only

#### Success Response (200 OK)

```json
{
  "id": 1,
  "name": "John Doe",
  "date_of_birth": "1990-05-15",
  "contact_info": "+1234567890",
  "user_id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```

---

### 10. Update Patient Profile

Update authenticated patient's profile.

**Endpoint**: `PATCH /api/v1/patients/profile/`  
**Authentication**: Required  
**Permissions**: Patient role only

#### Request Body

```json
{
  "name": "John Doe Updated",
  "date_of_birth": "1990-05-15",
  "contact_info": "+1234567890"
}
```

#### Success Response (200 OK)

Returns updated profile (same structure as GET)

---

### 11. Get Patient Submission History

Get all triage submissions for authenticated patient with pagination.

**Endpoint**: `GET /api/v1/patients/history/`  
**Authentication**: Required  
**Permissions**: Patient role only

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max 100) |

#### Success Response (200 OK)

```json
{
  "count": 45,
  "next": "http://localhost:8000/api/v1/patients/history/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "patient": 1,
      "symptoms": "Chest pain and shortness of breath",
      "priority": 1,
      "urgency_score": 95,
      "condition": "Acute Cardiac Event",
      "status": "completed",
      "photo_name": null,
      "created_at": "2026-04-29T08:00:00.000000Z",
      "processed_at": "2026-04-29T08:30:00.000000Z",
      "verified_by_user": 5,
      "verified_at": "2026-04-29T08:15:00.000000Z"
    }
  ]
}
```

---

### 12. Get Specific Submission Details

Get details of a specific submission.

**Endpoint**: `GET /api/v1/patients/submissions/{submission_id}/`  
**Authentication**: Required  
**Permissions**: Patient role only (own submissions)

#### Success Response (200 OK)

```json
{
  "id": 123,
  "patient": 1,
  "symptoms": "Chest pain and shortness of breath",
  "priority": 1,
  "urgency_score": 95,
  "condition": "Acute Cardiac Event",
  "status": "completed",
  "photo_name": null,
  "created_at": "2026-04-29T08:00:00.000000Z",
  "processed_at": "2026-04-29T08:30:00.000000Z",
  "verified_by_user": 5,
  "verified_at": "2026-04-29T08:15:00.000000Z"
}
```

#### Error Response (404 Not Found)

```json
{
  "code": "NOT_FOUND",
  "message": "Submission not found"
}
```

---

### 13. Get Current Active Session

Get patient's most recent active (non-completed) submission.

**Endpoint**: `GET /api/v1/patients/current/`  
**Authentication**: Required  
**Permissions**: Patient role only

#### Success Response - Active Session (200 OK)

```json
{
  "current_submission": {
    "id": 123,
    "symptoms": "Chest pain and shortness of breath",
    "priority": 1,
    "urgency_score": 95,
    "condition": "Acute Cardiac Event",
    "status": "in_progress",
    "photo_name": null,
    "created_at": "2026-04-29T08:00:00.000000Z",
    "processed_at": null
  },
  "message": "Active session found"
}
```

#### Success Response - No Active Session (200 OK)

```json
{
  "current_submission": null,
  "message": "No active session"
}
```

---

## Dashboard Endpoints (Staff Only)

### 14. Get Patient Queue

Get paginated patient queue with filtering.

**Endpoint**: `GET /api/v1/dashboard/staff/patients/`  
**Authentication**: Required  
**Permissions**: Medical staff only (nurse, doctor, admin)

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max 100) |
| `priority` | integer | - | Filter by priority (1-5) |
| `status` | string | - | Filter by status (waiting, in_progress, completed) |

#### Example Request

```
GET /api/v1/dashboard/staff/patients/?priority=1&status=waiting&page=1&page_size=20
```

#### Success Response (200 OK)

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/dashboard/staff/patients/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "patient_name": "John Doe",
      "description": "Chest pain and shortness of breath",
      "priority": 1,
      "urgency_score": 95,
      "condition": "Acute Cardiac Event",
      "status": "waiting",
      "photo_name": null,
      "verified_by_user": null,
      "verified_at": null,
      "created_at": "2026-04-29T08:00:00.000000Z"
    },
    {
      "id": 124,
      "patient_name": "Jane Smith",
      "description": "Severe abdominal pain",
      "priority": 1,
      "urgency_score": 90,
      "condition": "Acute Abdomen",
      "status": "waiting",
      "photo_name": null,
      "verified_by_user": null,
      "verified_at": null,
      "created_at": "2026-04-29T08:05:00.000000Z"
    }
  ]
}
```

**Queue Ordering Rules**:
1. Priority (ascending): 1 → 2 → 3 → 4 → 5
2. Within same priority, urgency_score (descending): 100 → 0
3. Within same priority and urgency, created_at (ascending): oldest first

---

### 15. Update Patient Status

Update patient's workflow status.

**Endpoint**: `PATCH /api/v1/dashboard/staff/patient/{id}/status/`  
**Authentication**: Required  
**Permissions**: Medical staff only

#### Request Body

```json
{
  "status": "in_progress"
}
```

**Valid Status Transitions**:
- `waiting` → `in_progress`
- `in_progress` → `completed`
- `waiting` → `completed` (skip in_progress)

#### Success Response (200 OK)

```json
{
  "message": "Status updated successfully"
}
```

#### Error Response (400 Bad Request)

```json
{
  "code": "INVALID_TRANSITION",
  "message": "Cannot transition from completed to waiting"
}
```

---

### 16. Update Patient Priority

Manually update patient's priority level.

**Endpoint**: `PATCH /api/v1/dashboard/staff/patient/{id}/priority/`  
**Authentication**: Required  
**Permissions**: Medical staff only

#### Request Body

```json
{
  "priority": 1
}
```

**Valid Priority Values**: 1 (critical) to 5 (non-urgent)

#### Success Response (200 OK)

```json
{
  "message": "Priority updated successfully"
}
```

**Note**: Priority updates trigger WebSocket broadcast to all connected staff clients.

#### Error Response (400 Bad Request)

```json
{
  "code": "INVALID_INPUT",
  "message": "Priority must be an integer between 1 and 5"
}
```

---

### 17. Verify Patient

Mark patient as verified by staff.

**Endpoint**: `PATCH /api/v1/dashboard/staff/patient/{id}/verify/`  
**Authentication**: Required  
**Permissions**: Medical staff only

#### Request Body

```json
{}
```

#### Success Response (200 OK)

```json
{
  "message": "Patient verified successfully"
}
```

#### Error Response (400 Bad Request)

```json
{
  "code": "ALREADY_VERIFIED",
  "message": "Patient already verified"
}
```

---

## Admin Endpoints (Staff Only)

### 18. Get System Overview

Get high-level system statistics.

**Endpoint**: `GET /api/v1/admin/overview/`  
**Authentication**: Required  
**Permissions**: Medical staff only

#### Success Response (200 OK)

```json
{
  "total_patients": 1250,
  "waiting_patients": 45,
  "in_progress_patients": 12,
  "completed_today": 87,
  "critical_cases": 3,
  "average_wait_time_minutes": 15.5
}
```

---

### 19. Get System Analytics

Get detailed system analytics and trends.

**Endpoint**: `GET /api/v1/admin/analytics/`  
**Authentication**: Required  
**Permissions**: Medical staff only

#### Success Response (200 OK)

```json
{
  "daily_submissions": [
    {"date": "2026-04-29", "count": 87},
    {"date": "2026-04-28", "count": 92},
    {"date": "2026-04-27", "count": 78}
  ],
  "priority_distribution": {
    "1": 15,
    "2": 30,
    "3": 45,
    "4": 25,
    "5": 10
  },
  "condition_breakdown": {
    "Cardiac": 20,
    "Respiratory": 35,
    "Trauma": 15,
    "Neurological": 10,
    "General": 45
  },
  "average_processing_time_minutes": 22.5,
  "staff_performance": [
    {"staff_id": 5, "name": "Dr. Smith", "patients_handled": 45},
    {"staff_id": 6, "name": "Nurse Johnson", "patients_handled": 38}
  ]
}
```

---

## WebSocket Events

### Connection

**URL**: `ws://localhost:8000/ws/triage/events/?token=<JWT_ACCESS_TOKEN>`  
**Protocol**: WebSocket  
**Authentication**: Required (JWT in query parameter)  
**Permissions**: Medical staff only (nurse, doctor, admin)

### Connection Example (JavaScript)

```javascript
const token = "eyJ0eXAiOiJKV1QiLCJhbGc...";
const ws = new WebSocket(`ws://localhost:8000/ws/triage/events/?token=${token}`);

ws.onopen = () => {
  console.log("WebSocket connected");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Event received:", data);
  
  switch(data.event_type) {
    case "patient_created":
      handleNewPatient(data);
      break;
    case "priority_update":
      handlePriorityUpdate(data);
      break;
    case "critical_alert":
      handleCriticalAlert(data);
      break;
    case "status_changed":
      handleStatusChange(data);
      break;
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket disconnected");
};
```

### Event Types

#### 1. Patient Created

Broadcast when a new patient submission is created.

```json
{
  "event_type": "patient_created",
  "patient_id": 123,
  "priority": 1,
  "urgency_score": 95,
  "timestamp": "2026-04-29T08:00:00.000000Z"
}
```

#### 2. Priority Update

Broadcast when a patient's priority is manually updated.

```json
{
  "event_type": "priority_update",
  "patient_id": 123,
  "old_priority": 3,
  "new_priority": 1,
  "urgency_score": 95,
  "timestamp": "2026-04-29T08:15:00.000000Z"
}
```

#### 3. Critical Alert

Broadcast when a critical case (Priority 1) is created.

```json
{
  "event_type": "critical_alert",
  "patient_id": 123,
  "priority": 1,
  "urgency_score": 95,
  "condition": "Acute Cardiac Event",
  "timestamp": "2026-04-29T08:00:00.000000Z"
}
```

#### 4. Status Changed

Broadcast when a patient's status changes.

```json
{
  "event_type": "status_changed",
  "patient_id": 123,
  "old_status": "waiting",
  "new_status": "in_progress",
  "timestamp": "2026-04-29T08:10:00.000000Z"
}
```

### Connection Errors

**401 Unauthorized - Invalid Token**
```json
{
  "error": "Invalid or expired token"
}
```

**403 Forbidden - Insufficient Permissions**
```json
{
  "error": "WebSocket access restricted to medical staff"
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {}
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `AUTHENTICATION_FAILED` | 401 | Invalid credentials |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_TRANSITION` | 400 | Invalid status transition |
| `INVALID_INPUT` | 400 | Invalid input value |
| `ALREADY_VERIFIED` | 400 | Patient already verified |
| `TRIAGE_ERROR` | 502 | Triage service failure |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

### Error Examples

**Validation Error**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid registration data",
  "details": {
    "username": ["This field is required."],
    "email": ["Enter a valid email address."]
  }
}
```

**Authentication Error**
```json
{
  "code": "AUTHENTICATION_FAILED",
  "message": "Invalid username or password"
}
```

**Permission Error**
```json
{
  "code": "FORBIDDEN",
  "message": "You do not have permission to perform this action"
}
```

---

## Rate Limiting & Pagination

### Rate Limiting

**Current Status**: Not implemented  
**Planned**: 100 requests per minute per user

### Pagination

All list endpoints support pagination with the following parameters:

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | - | Page number |
| `page_size` | integer | 20 | 100 | Items per page |

#### Pagination Response Format

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/endpoint/?page=2",
  "previous": null,
  "results": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of items |
| `next` | string/null | URL to next page (null if last page) |
| `previous` | string/null | URL to previous page (null if first page) |
| `results` | array | Array of items for current page |

---

## Status Codes

### Success Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PATCH requests |
| 201 | Created | Successful POST requests creating resources |
| 204 | No Content | Successful DELETE requests |

### Client Error Codes

| Code | Description | Usage |
|------|-------------|-------|
| 400 | Bad Request | Invalid input, validation errors |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Semantic errors in request |

### Server Error Codes

| Code | Description | Usage |
|------|-------------|-------|
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | External service failure (AI, database) |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Additional Resources

- **Main Documentation**: [README.md](README.md)
- **AI Service Guide**: [AI_SERVICE_USAGE_GUIDE.md](AI_SERVICE_USAGE_GUIDE.md)
- **Queue Priority System**: [QUEUE_PRIORITY_SYSTEM_DOCUMENTATION.md](QUEUE_PRIORITY_SYSTEM_DOCUMENTATION.md)
- **Test Documentation**: [TEST_FIXES_SUMMARY.md](TEST_FIXES_SUMMARY.md)

---

## Support

- **Email**: support@triagesync.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/triagesync/issues)
- **Documentation**: [Full Documentation](https://docs.triagesync.com)

---

**Built with ❤️ for better healthcare**

**Version**: 1.0.0  
**Last Updated**: April 29, 2026  
**Status**: Production Ready ✅
