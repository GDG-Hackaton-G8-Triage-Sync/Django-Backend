# Authentication & User Roles

TriageSync uses a robust JWT-based authentication system with strict role-based access control (RBAC).

## 🔐 Authentication Flow

### 1. Token-Based Access
All protected endpoints require a valid JWT Access Token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### 2. Token Lifecycle
- **Access Token**: Short-lived (Default: 60 mins) for security.
- **Refresh Token**: Long-lived (Default: 7 days) used to obtain new access tokens.
- **Rotation**: Refresh tokens are rotated upon use to prevent replay attacks.

---

## 👥 User Roles & Permissions

| Role | Access Level | Description |
| :--- | :--- | :--- |
| **Patient** | Restricted | Can submit symptoms, view personal history, and manage their own profile. |
| **Nurse** | Staff | Can view the triage queue, update patient status, and verify cases. |
| **Doctor** | Staff | Full access to patient queue, clinical notes, and verification. |
| **Admin** | Superuser | System-wide access, user management, analytics, and system configuration. |

---

## 🛠️ Core Auth Endpoints

### Register User
`POST /api/v1/auth/register/`

Registers a new user. For **Patients**, the following demographic fields are mandatory for AI triage accuracy:
- `age`: integer (0-150)
- `gender`: string (male/female/other)
- `blood_type`: string (A+, O-, etc.)

### Login
`POST /api/v1/auth/login/`

**Returns**:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "role": "patient",
  "user_id": 123,
  "name": "John Doe"
}
```

### Refresh Token
`POST /api/v1/auth/refresh/`
**Body**: `{"refresh": "<refresh_token>"}`

---

## 🚧 Security Best Practices

1. **Secure Storage**: Never store JWTs in `localStorage` in web apps. For Flutter, use `flutter_secure_storage`.
2. **Interceptors**: Implement a 401 interceptor to handle automatic token refreshing.
3. **Role Validation**: Always check the `role` field in the login response to determine which UI modules to enable.
