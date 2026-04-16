# Django-Backend 

# Overview

Triage Sync is a system designed to **synchronize patient triage updates in real time** across different services. The system allows healthcare staff to submit patient triage information, which is then processed, validated, and broadcast to connected clients instantly.

The system uses **Django**, **Redis**, and **WebSocket** to enable secure and real-time communication.

# System Architecture

The system is composed of several modules that work together.

Client
   │
   │ Submit triage data
   ▼
API (Django REST)
   │
   ├ Security validation
   ├ Payload validation
   ▼
Submission Trigger
   │
   ▼
Logic Trigger
   │
   ▼
AI Service Layer
   │
   ▼
Redis Pub/Sub
   │
   ▼
WebSocket Broadcast
   │
   ▼
Connected Clients receive update

# 1. Payload Format 

The payload format defines the **structure of the data exchanged between systems**.

The system accepts patient triage data in JSON format.

Payload validation is handled using serializers in Django REST Framework.

Purpose of payload format:

* Ensure consistent data structure
* Prevent invalid data from entering the system
* Simplify integration with other services

---

# 2. Security Layer 

Security ensures that **only authorized users can access the system**.

The system uses **JWT authentication**.

Security process:

1. User logs into the system.
2. The server generates an authentication token.
3. The client includes the token in every request.
4. The server verifies the token before processing the request.

Security protections include:

* Authentication using JWT tokens
* Role-based authorization (doctor, nurse, admin)
* Input validation
* Secure HTTPS communication

Example request header:

This prevents unauthorized users from submitting or modifying triage data.

---

# 3. Submission Trigger

The submission trigger activates when **new triage data is submitted**.

Workflow:

1. A user submits triage data through the API.
2. The API validates the payload.
3. If validation is successful, the submission trigger fires.

Purpose:

* Detect new triage submissions
* Initiate system processing
* Notify other components that new data is available

This acts as the **starting point of the system workflow**.

---

# 4. Logic Trigger

The logic trigger performs **business logic processing** after a submission occurs.

Processing may include:

* Assigning urgency levels
* Checking patient conditions
* Updating triage status
* Forwarding data to AI analysis

Example logic:

* If symptoms include chest pain → mark priority high
* If symptoms include mild fever → mark priority medium

This step ensures that triage data is **interpreted and processed correctly**.

---

# 5. AI Service Layer

The AI service layer analyzes triage data to **assist in decision-making**.

The AI service may perform:

* Symptom analysis
* Risk prediction
* Priority recommendations
* Alert generation

 Example AI functionality:

* Detect high-risk symptoms
* Recommend priority level
* Flag critical patients


The AI layer improves system intelligence and supports healthcare staff in making faster triage decisions.

---

# 6. Redis Configuration (M8)

Redis is used as a **message broker for real-time communication**.

The system uses Redis Pub/Sub to distribute updates.

Purpose of Redis:

* Store temporary messages
* Manage event streams
* Enable fast message delivery between services

Workflow:

1. Backend publishes triage updates to Redis.
2. Redis broadcasts the update to subscribers.
3. WebSocket server receives the message.

Redis ensures that updates are delivered quickly and efficiently.

---

# 7. WebSocket Setup 

WebSockets allow **real-time communication between the server and clients**.

Unlike traditional HTTP requests, WebSockets maintain a **persistent connection**.

WebSocket workflow:

1. Client establishes WebSocket connection.
2. Server authenticates the client.
3. Server listens for Redis messages.
4. When a triage update occurs, the server broadcasts the update.
5. All connected clients receive the update instantly.

Example uses:

* Real-time patient status updates
* Emergency alerts
* Live triage dashboards

---

# 8. Integration and Debugging (M1)

Integration ensures that **all system components work together correctly**.

Steps in integration:

1. Connect Django API with Redis.
2. Connect Redis with WebSocket server.
3. Connect WebSocket server with clients.
4. Integrate AI service layer with backend logic.

Debugging activities include:

* Monitoring logs
* Checking Redis message flow
* Testing WebSocket connections
* Verifying payload validation
* Testing security authentication

Integration testing ensures that the system operates reliably.

---

# System Workflow Summary

1. A user submits triage data.
2. The system validates payload format.
3. Security checks authenticate the user.
4. Submission trigger activates system processing.
5. Logic trigger performs triage analysis.
6. AI service layer analyzes patient data.
7. Redis publishes the triage update.
8. WebSocket broadcasts updates to connected clients.
9. Clients receive real-time triage updates.

---

# Key Technologies

* Django – Backend API
* Django REST Framework – API development
* Redis – Message broker
* WebSocket – Real-time communication
* JSON – Data payload format

---

# Conclusion

Triage Sync provides a **secure, real-time system for managing and synchronizing patient triage updates**. By combining Django APIs, Redis messaging, WebSocket communication, and AI analysis, the system enables healthcare staff to receive timely information and respond to critical cases efficiently.


