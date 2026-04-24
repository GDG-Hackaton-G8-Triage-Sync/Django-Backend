# Django-Backend
# TriageSync – Member 7 Data Layer (Queries)

## Overview

This module implements the **Data Access Layer** for the TriageSync system.
It provides optimized database queries used by the API layer to manage triage sessions, queue ordering, and priority updates.

This work corresponds to **Member 7 — Data Layer (Models & Queries)**.

The queries operate on models defined in:

* `authentication/models.py`
* `patients/models.py`
* `triage/models.py`

---

## Responsibilities

This module handles:

* Fetching staff queue
* Sorting patients by urgency
* Getting patient session details
* Creating triage sessions
* Overriding priority
* Reordering queue positions

All logic is implemented inside:

```
triage/services.py
```

---

## Project Structure

```
Triagesync/
│
├── authentication/
│   └── models.py
│
├── patients/
│   └── models.py
│
├── triage/
│   ├── models.py
│   └── services.py   ← Data Layer (Member 7)
│
├── manage.py
└── db.sqlite3
```

---

## Functions Implemented

### 1. Get Staff Queue

Returns all pending triage sessions sorted by urgency score.

```python
get_staff_queue()
```

Used by:

* Staff dashboard
* Queue display

---

### 2. Get Current Session

Returns the latest session for a patient.

```python
get_current_session(patient)
```

Used by:

* Patient status screen

---

### 3. Get Patient Detail

Fetches a single triage session by session ID.

```python
get_patient_detail(session_id)
```

Used by:

* Staff patient detail view

---

### 4. Override Priority

Allows staff to manually override priority level.

```python
override_priority(session_id, new_priority)
```

Automatically reorders queue after update.

---

### 5. Reorder Queue

Recalculates queue positions based on urgency score.

```python
reorder_queue()
```

Highest urgency → position 1

---

### 6. Create Triage Session

Creates a new triage session for a patient.

```python
create_triage_session(patient, symptoms)
```

Status defaults to:

```
pending
```

---

## Queue Ordering Logic

Queue is sorted using:

```
urgency_score DESC
```

Example:

| Patient          | Urgency | Position |
| ---------------- | ------- | -------- |
| Chest Pain       | 95      | 1        |
| Shortness Breath | 80      | 2        |
| Fever            | 40      | 3        |

---

## Dependencies

* Django
* Django ORM
* SQLite / PostgreSQL

---

## Testing

Run Django shell:

```
python manage.py shell
```

Import services:

```
from triage.services import *
```

Test queue:

```
get_staff_queue()
```

---

## Integration

This module is used by:

* API views
* Staff dashboard endpoints
* Patient submission endpoints

Example usage:

```
sessions = get_staff_queue()
```

---

## Author

Member 7 — Data Layer
Queries & Database Access Logic

Nardos
