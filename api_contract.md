# API Contract Documentation – TriageSync Backend

## 1. Base Information
- **Base URL:** https://your-domain.com/api/
- **Authentication Type:** JWT (JSON Web Token)
- **Headers (Required for protected routes):**
  ```json
  {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
  }
  ```

## 2. Authentication API
### 2.1 Login
- **Endpoint:** POST /api/auth/login/
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "123456"
  }
  ```
- **Response (Success):**
  ```json
  {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "role": "patient"
  }
  ```
- **Response (Failure):**
  ```json
  {
    "error": "Invalid credentials"
  }
  ```

### 2.2 Refresh Token
- **Endpoint:** POST /api/auth/refresh/
- **Request:**
  ```json
  {
    "refresh_token": "token"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "new_access_token"
  }
  ```

## 3. Patient Submission API
### 3.1 Submit Symptoms
- **Endpoint:** POST /api/triage/
- **Access:** Patient only, JWT required
- **Request Body:**
  ```json
  {
    "description": "Chest pain and sweating for 30 minutes"
  }
  ```
- **Validation Rules:**
  - Max length: 500 characters
  - Cannot be empty
- **Response (Success):**
  ```json
  {
    "id": 101,
    "priority": 1,
    "urgency_score": 95,
    "condition": "Cardiac Event",
    "status": "processed",
    "created_at": "2026-04-14T10:30:00Z"
  }
  ```
- **Response (AI Fallback):**
  ```json
  {
    "id": 101,
    "priority": 3,
    "urgency_score": 50,
    "condition": "Unknown - Needs Review",
    "status": "fallback"
  }
  ```

## 4. Dashboard API
### 4.1 Get All Patients
- **Endpoint:** GET /api/patients/
- **Access:** Staff only, JWT required
- **Response:**
  ```json
  [
    {
      "id": 101,
      "description": "Chest pain...",
      "priority": 1,
      "urgency_score": 95,
      "condition": "Cardiac Event",
      "created_at": "2026-04-14T10:30:00Z"
    },
    {
      "id": 102,
      "description": "Headache...",
      "priority": 3,
      "urgency_score": 60,
      "condition": "Migraine"
    }
  ]
  ```
- **Sorting Rule:** urgency_score DESC

## 5. AI Triage Internal Pipeline
- **AI Input Format:**
  ```json
  {
    "description": "string"
  }
  ```
- **AI Output (Strict Format):**
  ```json
  {
    "priority": 1-5,
    "urgency_score": 0-100,
    "condition": "string"
  }
  ```
- **Rules:**
  - Must return JSON only
  - No explanations
  - No extra text
  - Invalid output triggers fallback system

## 6. Real-Time WebSocket API
- **Connection:** ws://your-domain.com/ws/triage/
- **Auth:** First message after connect:
  ```json
  {
    "token": "jwt_token_here"
  }
  ```
- **Event: NEW PATIENT UPDATE (Server → Client):**
  ```json
  {
    "type": "patient_update",
    "data": {
      "id": 101,
      "priority": 1,
      "urgency_score": 95,
      "condition": "Cardiac Event"
    }
  }
  ```
- **Event Types:**
  | Event           | Description                |
  |-----------------|---------------------------|
  | patient_update  | New patient added         |
  | triage_update   | AI processed result       |
  | system_alert    | Critical patient warning  |

## 7. Error Handling Standard
- **401 Unauthorized:**
  ```json
  { "error": "Unauthorized access" }
  ```
- **403 Forbidden:**
  ```json
  { "error": "Permission denied" }
  ```
- **400 Validation Error:**
  ```json
  {
    "error": "Invalid input",
    "details": {
      "description": "Cannot exceed 500 characters"
    }
  }
  ```
- **500 Server Error:**
  ```json
  { "error": "Internal server error" }
  ```

## 8. System Behavior Rules
- **Triage Rules:**
  - Priority 1 = Critical (life-threatening)
  - Priority 5 = Low urgency
- **Sorting Rule:** urgency_score DESC
- **Real-time Rule:** Update latency < 1 second; every new triage triggers WebSocket broadcast
- **Data Storage Rule:** Every submission stores description, AI output, timestamp, priority, urgency_score

## 9. End-to-End Flow
1. Patient logs in (JWT issued)
2. Patient submits symptoms
3. Backend validates input
4. AI processes symptom
5. Triage engine assigns priority
6. Data stored in DB
7. WebSocket broadcasts update
8. Staff dashboard updates instantly

---
This API contract ensures frontend-backend alignment, clean Django implementation, stable AI integration, safe fallback behavior, real-time update consistency, and hackathon-ready demo stability.
