# Django-Backend
# TriageSync – Member-7 Data Models

## Overview

This module implements the **Data Models** for the TriageSync system.  
It defines the core database entities used by the API layer to manage authentication, patient records, and triage sessions.

This work corresponds to **Member 7-Data Models**.

The models are defined in:

* `authentication/models.py`
* `patients/models.py`
* `triage/models.py`

---

## Responsibilities

This module handles:

* User authentication and role management
* Patient record storage
* Triage session tracking
* File uploads and AI results storage

---

## Project Structure
Triagesync/
│
├── authentication/
│   └── models.py   ← Authentication model
│
├── patients/
│   └── models.py   ← Patient model
│
├── triage/
│   └── models.py   ← Triage session model
│
├── manage.py
└── db.sqlite3

---

## Models Implemented

### 1. Authentication Model
Defines a custom `User` model with role choices (e.g., staff, patient).

### 2. Patient Model
Stores patient details and submission records.

### 3. Triage Session Model
Tracks triage sessions, urgency, AI results, and file uploads.

---

## Current Status

- Models created and migrations generated.
- Code committed to `nebiyat-models` branch.

---

## Next Steps

- Test models with local database.
- Add API endpoints for patient and triage workflows.
- Integrate with frontend dashboard.


