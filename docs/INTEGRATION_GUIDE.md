# Frontend Integration Guide (Flutter)

This guide provides specific implementation patterns for integrating the TriageSync backend into a Flutter mobile application.

## 🏗️ Data Models

### Updated TriageItem Model
Ensure your frontend model includes the newer clinical and AI fields for the **Patient Detail** screen.

```dart
class TriageItem {
  final int id;
  final String status;          // waiting, in_progress, completed
  final int priority;          // 1 (Critical) to 5 (Routine)
  final double confidence;     // 0.0 to 1.0 (Multiply by 100 for UI)
  
  // Patient Demographics
  final String patientName;
  final int? patientAge;
  final String? bloodType;
  final String? medicalHistory;
  final String? allergies;

  // AI Reasoning
  final String condition;      // e.g. "Acute Coronary Syndrome"
  final String reason;         // Full sentence clinical rationale
  final List<String> explanation; // List of key symptom findings
  
  // ... constructors and fromJson mapping ...
}
```

---

## 🔐 Authentication & Permissions

### Role-Based Views
- **Patients**: Should only access `/api/v1/triage/` (POST) and `/api/v1/patients/submissions/{id}/` (GET - restricted to own ID).
- **Staff/Admins**: Have full access to the **Patient Queue** and **Patient Detail** clinical views.

### Permission Fix (April 2026 Update)
The backend now allows **Admins** and **Staff** to view the `PatientSubmissionDetailView`. Ensure your app checks the `role` from the login response to toggle the "Confirm AI Priority" and "Assign Staff" buttons.

---

## 🗺️ Staff Clinical Workflow — URL Reference

The Flutter frontend uses the `/api/v1/staff/` prefix for all clinical workflow actions. These routes are fully supported:

| Action | Method | URL |
| :----- | :----- | :-- |
| Get staff notes | `GET` | `/api/v1/staff/patient/{id}/notes/` |
| Add staff note | `POST` | `/api/v1/staff/patient/{id}/notes/` |
| Assign staff to case | `PATCH` | `/api/v1/staff/patient/{id}/assign/` |
| View vitals history | `GET` | `/api/v1/staff/patient/{id}/vitals/history/` |
| Verify triage case | `PATCH` | `/api/v1/staff/patient/{id}/verify/` |

> **Note**: The same views are also accessible under `/api/v1/triage/{id}/` (e.g. `notes/`, `assign/`, `vitals/`) for backwards compatibility.

---

## 📡 Real-time Handling

### WebSocket Connection
**Path**: `ws://<HOST>/ws/triage/events/?token=<JWT>`

### PING/PONG (Heartbeat)
The backend uses Daphne (ASGI). It is recommended that the Flutter app sends a heartbeat message or uses the `pingInterval` in `WebSocketChannel` to keep connections alive in production environments.

---

## 🚀 Development Tips

1. **AI Reasoning**: On the **Patient Detail** screen, if `confidence < 0.5`, display a warning icon suggesting immediate manual review.
2. **Emergency Flags**: If `is_critical` is true, pulse the UI in red.
3. **Staff Names**: Use the `assigned_staff_name` field to show which nurse or doctor is currently handling the case.
