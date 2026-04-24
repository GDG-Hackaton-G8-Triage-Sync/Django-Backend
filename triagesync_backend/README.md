# 🏥 TriageSync - Member 6 (Triage Logic Service)

## 📌 Overview
This module is responsible for the **core triage decision engine** of the TriageSync system.  
It processes patient symptoms and generates urgency-based medical priorities.

---

## ⚙️ Features Implemented

### 1. Symptom Validation
- Ensures input symptoms are clean and valid before processing.

### 2. AI-Based Priority Inference
- Uses AI service to generate a base urgency score.

### 3. Urgency Scoring System
- Converts symptoms into a numerical urgency score (0–100).

### 4. Priority Mapping
- Score is mapped into priority levels:
  - CRITICAL (80–100)
  - URGENT (60–79)
  - MEDIUM (40–59)
  - STABLE (0–39)

### 5. Status Transitions
- Tracks patient state:
  - PENDING → TRIAGED → ESCALATED → STABLE

### 6. Emergency Override System
- Detects life-threatening keywords (e.g., chest pain, unconscious)
- Immediately escalates to CRITICAL status.

### 7. Event Trigger System
- Generates system events based on triage result:
  - EMERGENCY_ALERT
  - URGENT_ALERT
  - LOG_ONLY

---

## 🔁 Workflow

1. Input symptoms
2. Validate input
3. AI generates urgency score
4. Apply business rules
5. Update status
6. Trigger event
7. Return structured response

---

## 🧪 Test Cases

Example inputs:
- "Severe chest pain and difficulty breathing"
- "High fever and vomiting"
- "Mild headache"
- "Patient is unconscious"
- "Feeling dizzy and tired"

---

## 📦 Output Format

```json
{
  "success": true,
  "data": {
    "triage_result": {},
    "event": {},
    "source": "AI_SYSTEM | EMERGENCY_OVERRIDE",
    "module": "member6_triage_service"
  }
}
