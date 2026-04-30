# TriageSync API Reference

**Version**: 1.2.0 | **Env**: Development & Production  
**Base URL (Dev)**: `http://localhost:8000/api/v1`  
**Base URL (Prod)**: `https://django-backend-4r5p.onrender.com/api/v1`

---

## 🔒 1. Authentication

TriageSync implements JWT (JSON Web Token) authentication. Secured endpoints require a valid token passed in the `Authorization` header.

**Header Format**:
`Authorization: Bearer <access_token>`

**Lifecycle**:

- `Access Token`: 60 minutes
- `Refresh Token`: 7 days
- `Refresh Endpoint`: `/auth/refresh/`

### User Roles & Permissions

| Role      | Description                 | Access Scope              |
| --------- | --------------------------- | ------------------------- |
| `patient` | Individual submitting forms | Patient-scoped endpoints  |
| `nurse`   | Unit queue management       | Staff + Admin reads       |
| `doctor`  | Full medical intervention   | Staff + Admin full access |
| `admin`   | System configuration        | Global access             |

## 🚀 2. Core Endpoints

### Auth Services

- `POST /auth/login/` - Authenticate and receive JWT tokens.
- `POST /auth/refresh/` - Refresh an expired access token.
- `POST /auth/register/` - Register a new user profile.

### Triage & Patients

- `POST /triage/` - Submit patient symptoms for assessment (AI integration triggers here).
- `GET /patients/` - (Staff) Retrieve global patient queue log.
- `GET /patients/{id}/` - (Staff) Retrieve specific patient details.
- `PATCH /patients/{id}/status/` - Update a patient's triage state.

### Dashboards (Role-Gated)

- `GET /dashboard/staff/patients/` - Operational queue for Nurses and Doctors.
- `GET /dashboard/admin/overview/` - High-level metrics for administrative management.

## ⚠️ 3. Standardized Error Handling

The API uniformly returns JSON error shapes for predictability based on standard HTTP status codes:

- `200/201`: Success / Created
- `400`: Bad Request (Validation errors)
- `401`: Unauthorized (Invalid or missing JWT)
- `403`: Forbidden (Insufficient role permissions)
- `404`: Resource not found
- `500`: Internal Server Error

**Error Payload Standard**:

```json
{
    "error": "code_reference_string",
    "detail": "Human readable description of the error."
}
```
