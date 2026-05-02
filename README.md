# TriageSync Backend

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-green.svg)
![Mode](https://img.shields.io/badge/engine-ASGI/Daphne-orange.svg)

TriageSync is an AI-powered medical triage platform that helps healthcare facilities prioritize patient care through intelligent symptom analysis and real-time monitoring.

## 🚀 Latest Updates (May 2026)

- **⚡ Asynchronous Support**: The server now runs on **ASGI (Daphne)**, supporting concurrent WebSocket connections and non-blocking real-time events.
- **🧠 Enriched AI Reasoning**: Triage results now include **Confidence Scores (0-100%)**, clinical rationale, and symptom extraction.
- **👨‍⚕️ Advanced Staff Tools**: Improved permissions allowing Admins and Staff to view full Clinical Profiles and manage staff assignments.
- **📊 Command Center Analytics**: Real-time hourly trends for Wait Times and SLA Breach Velocity.

## 📖 Documentation Index

For detailed information, please refer to the specialized guides in the `/docs` directory:

- [**Authentication & Roles**](./docs/AUTH_&_USER_ROLES.md) - JWT, RBAC, and Security.
- [**API Reference**](./docs/API_REFERENCE.md) - Enriched TriageItem schema and endpoints.
- [**Real-time & Notifications**](./docs/REALTIME_&_NOTIFICATIONS.md) - WebSockets and dual-channel push.
- [**Flutter Integration**](./docs/INTEGRATION_GUIDE.md) - Mobile-specific data models and logic.
- [**AI System**](./docs/AI_SYSTEM.md) - Gemini reasoning, Redundancy, and Confidence.

---
Built with ❤️ by the TriageSync Team.
