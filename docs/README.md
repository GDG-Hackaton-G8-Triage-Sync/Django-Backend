# TriageSync Project Documentation

Welcome to the TriageSync backend documentation. This project is a specialized medical triage system using AI to prioritize patient cases.

## 📚 Documentation Index

### 1. [Authentication & User Roles](./AUTH_&_USER_ROLES.md)
Detailed information on JWT authentication, registration, login, and the role-based access control system (Patient, Nurse, Doctor, Admin).

### 2. [API Reference](./API_REFERENCE.md)
A comprehensive guide to all REST endpoints, including request/response examples for Patient, Staff, and Admin workflows.

### 3. [Real-time Events & Notifications](./REALTIME_&_NOTIFICATIONS.md)
Documentation for WebSocket connections, broadcast events (patient updates, critical alerts), and the persistent notification system.

### 4. [Frontend Integration Guide](./INTEGRATION_GUIDE.md)
Standard operating procedures for Flutter integration, including JWT state management, interceptors, and suggested data models.

### 5. [AI Triage System](./AI_SYSTEM.md)
Insights into the Gemini AI integration, triage logic, priority levels (1-5), and emergency override mechanisms.

---

## 🚀 Quick Start for Developers

1. **Environment Setup**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database & Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Running the Server**
   ```bash
   python manage.py runserver
   ```

4. **Running Tests**
   ```bash
   pytest
   ```

---
**Version**: 2.0.0  
**Status**: Production Ready ✅
