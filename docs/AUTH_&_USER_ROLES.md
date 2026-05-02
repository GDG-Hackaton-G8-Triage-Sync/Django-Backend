# Authentication & User Roles

TriageSync uses a robust JWT-based authentication system with strict role-based access control (RBAC).

## 👥 User Roles & Permissions

| Role | Access Level | Description |
| :--- | :--- | :--- |
| **Patient** | Restricted | Can submit symptoms and view **their own** medical history. |
| **Nurse** | Clinical Staff| Can view the triage queue, update status, and verify cases. |
| **Doctor** | Clinical Staff| Full clinical access including notes, vitals, and assignment. |
| **Admin** | System Admin | Full access to Dashboard Analytics, User Management, and Audit Logs. |

### 🛠️ Permission Note for Developers
As of the latest update, **Admins** have been granted full clinical visibility. This means an Admin user can establish WebSocket connections to the triage group and access individual patient detail records, just like a Doctor or Nurse.

---

## 🛠️ Core Auth Endpoints

### Register User
`POST /api/v1/auth/register/`

### Login
`POST /api/v1/auth/login/`
**Returns**:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "role": "admin",
  "user_id": 12,
  "name": "Admin User"
}
```

### Refresh Token
`POST /api/v1/auth/refresh/`

---

## 🚧 Account Suspension
The backend supports account suspension. 
- **Trigger**: Handled via `PATCH /api/v1/admin/users/{id}/suspend/`.
- **Behavior**: Suspended users will receive a 403 Forbidden on all API calls and will be disconnected from WebSockets with Close Code 4003.
