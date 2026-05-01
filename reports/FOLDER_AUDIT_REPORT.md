# 📁 Detailed Folder-by-Folder Audit Report

**Date:** 2026-04-28  
**Branch:** feature/AI_service  
**Scope:** Complete architectural review of all apps

---

## 🎯 Executive Summary

**Total Issues Found:** 32  
- 🔴 **Critical Architectural Issues:** 8
- 🟡 **Misplaced Code:** 12  
- 🟢 **Code Quality Issues:** 12

---

## 📁 FOLDER 1: AUTHENTICATION (Member 2)

**Owner:** Member 2  
**Responsibility:** JWT login & refresh, Role system, Permission classes, WebSocket auth

### ✅ What's Good:
- Clean permission classes (IsPatient, IsStaff, IsAdmin, etc.)
- Proper service layer separation (auth_service.py)
- Good serializer structure

### 🔴 Critical Issues:

#### 1. **Response Format Violates API Contract**
**Location:** `authentication/views.py` lines 20, 38  
**Problem:**
```python
return success_response({
    "user": serializer.data,
    "tokens": tokens  # ❌ Wrong structure
})
```

**API Contract Expects (Section 2.1):**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "role": "patient",
  "user_id": 123,
  "name": "...",
  "email": "..."
}
```

**Fix:**
```python
return Response({
    "access_token": tokens['access'],
    "refresh_token": tokens['refresh'],
    "role": user.role,
    "user_id": user.id,
    "name": user.username,
    "email": user.email
}, status=status.HTTP_201_CREATED)
```

#### 2. **Using `success_response()` Creates Envelope**
**Location:** `authentication/views.py`  
**Problem:** `success_response()` from core adds wrapper, but API contract says "no success envelope"

**Fix:** Use direct `Response()` from DRF

#### 3. **Missing Refresh Token Endpoint**
**Location:** `authentication/urls.py`  
**API Contract:** `POST /api/v1/auth/refresh/`  
**Status:** ❌ Not implemented

### 🟡 Medium Issues:

#### 4. **Inconsistent Permission Class Names**
**Location:** `authentication/permissions.py`  
**Problem:**
- `IsDoctor` checks `role == 'doctor'`
- `IsNurse` calls `is_nurse()` method
- `IsStaff` checks `role in ['nurse', 'doctor', 'staff']`

**Issue:** API contract uses "staff" not "doctor/nurse". Inconsistent.

**Fix:** Standardize to match API contract roles:
```python
class IsStaff(BasePermission):
    """Staff = nurse OR doctor"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['staff', 'nurse', 'doctor']
        )
```

#### 5. **Missing WebSocket Authentication Middleware**
**Location:** Task Classification says Member 2 owns "WebSocket authentication middleware"  
**Status:** ❌ Not found anywhere

**Fix:** Create `authentication/middleware/websocket_auth.py`

### 🟢 Minor Issues:

#### 6. **No Email Validation in RegisterSerializer**
**Location:** `authentication/serializers.py`  
**Fix:** Add email field and validation

#### 7. **Password Not Hashed Explicitly**
**Location:** `authentication/serializers.py` line 12  
**Current:** Relies on `create_user()` to hash  
**Better:** Explicitly call `set_password()`

---

## 📁 FOLDER 2: PATIENTS (Member 3)

**Owner:** Member 3  
**Responsibility:** POST /api/triage/, Input validation, Start processing pipeline, Emit "new patient" event

### 🔴 Critical Issues:

#### 8. **WRONG LOCATION: Patient API in Wrong Folder**
**Location:** `patients/views.py` - `PatientTriageView`  
**Problem:** This is the **main triage submission endpoint** but it's in the `patients` app!

**API Contract:** `POST /api/v1/triage/`  
**Current URL:** `POST /api/v1/patients/patient/triage/` ❌

**Why Wrong:**
- Task Classification: Member 3 owns "POST /api/triage/" but it should be mounted at `/api/v1/triage/`
- The `patients` app should be for **patient profile management**, not triage submission
- Triage submission is a **triage operation**, not a patient operation

**Fix:** Move `PatientTriageView` to `triage/views.py` and mount at `/api/v1/triage/`

#### 9. **Missing Model: `TriageItem` Doesn't Exist**
**Location:** `patients/views.py` line 13  
**Problem:**
```python
from apps.triage.models import TriageItem  # ❌ This model doesn't exist!
```

**What Exists:**
- `TriageSession` (triage/models.py)
- `PatientSubmission` (patients/models.py)

**Fix:** Use `PatientSubmission` model

#### 10. **Broken Function Calls**
**Location:** `patients/views.py` lines 27-28  
**Problem:**
```python
ai_result = analyze_symptoms(symptoms)  # ❌ Function doesn't exist
triage_result = process_triage(ai_result)  # ❌ Wrong signature
```

**What Exists:**
- `evaluate_triage(symptoms: str)` in `triage/services/triage_service.py`

**Fix:**
```python
from apps.triage.services.triage_service import evaluate_triage
triage_result = evaluate_triage(symptoms)
```

#### 11. **Wrong Broadcast Function**
**Location:** `patients/views.py` line 31  
**Problem:**
```python
broadcast_new_triage({...})  # ❌ Function doesn't exist
```

**What Exists:**
- `broadcast_patient_created(patient_id, priority, urgency_score)`

**Fix:**
```python
from apps.realtime.services.broadcast_service import broadcast_patient_created
broadcast_patient_created(
    patient_id=submission.id,
    priority=triage_data["priority"],
    urgency_score=triage_data["urgency_score"]
)
```

### 🟡 Medium Issues:

#### 12. **Missing Services Folder**
**Location:** `patients/` app  
**Problem:** All logic is in views.py, no service layer

**Fix:** Create `patients/services/patient_service.py` for business logic

#### 13. **No Patient Profile Management**
**Location:** Entire `patients` app  
**Problem:** The app is called "patients" but has no patient profile CRUD operations

**API Contract Expects:**
- Patient profile management
- Patient history
- Patient details

**Current:** Only has triage submission (which shouldn't be here)

**Fix:** Add proper patient profile views:
- `GET /api/v1/patients/profile/`
- `PATCH /api/v1/patients/profile/`
- `GET /api/v1/patients/history/`

#### 14. **Wrong Field Name in Serializer**
**Location:** `patients/serializers.py` - `TriageSubmissionSerializer`  
**Problem:**
```python
symptoms = serializers.CharField(max_length=500)  # ❌ Should be "description"
```

**API Contract:** Field is called `"description"` not `"symptoms"`

### 🟢 Minor Issues:

#### 15. **No Permission Class on PatientTriageView**
**Location:** `patients/views.py` line 11  
**Current:** `permission_classes = [IsAuthenticated]`  
**Should Be:** `permission_classes = [IsAuthenticated, IsPatient]`

#### 16. **Unused Imports**
**Location:** `patients/views.py`  
**Problem:** Imports that reference non-existent code

---

## 📁 FOLDER 3: TRIAGE (Member 5 & 6)

**Owners:** Member 5 (AI Service), Member 6 (Triage Logic)  
**Responsibilities:**
- M5: Call OpenAI/Gemini, Build prompts, Parse response
- M6: Urgency score, Priority mapping, Fallback system, Status transitions, Event triggers

### 🔴 Critical Issues:

#### 17. **DUPLICATE URL FILES**
**Location:** `triage/` folder  
**Problem:**
```
triage/url.py    ← Old file (3 lines)
triage/urls.py   ← New file (7 lines)
```

**Impact:** Confusing, `config/urls.py` includes `triage.urls` (with 's'), so `url.py` is dead code

**Fix:** Delete `triage/url.py`

#### 18. **MISPLACED: Middleware in Wrong App**
**Location:** `triage/middleware.py`  
**Problem:** This is **request sanitization middleware** that should be in `core/` app (Member 1's territory)

**Why Wrong:**
- Task Classification: Member 1 owns "Shared validators" and "Helper utilities"
- Middleware that runs on ALL requests should be in `core/`, not `triage/`
- It's not triage-specific logic, it's input hygiene

**Fix:** Move to `core/middleware/payload_sanitizer.py`

#### 19. **Wrong Endpoint Path**
**Location:** `triage/urls.py` line 7  
**Problem:**
```python
path("triage/", TriageEvaluateView.as_view())  # Results in /api/v1/triage/triage/
```

**Fix:**
```python
path("", TriageEvaluateView.as_view())  # Results in /api/v1/triage/
```

#### 20. **Multiple Triage Endpoints (Confusion)**
**Location:** `triage/urls.py`  
**Problem:**
```python
path('ai/', TriageAIView.as_view()),           # What's this?
path('pdf-extract/', TriagePDFExtractView.as_view()),  # What's this?
path("triage/", TriageEvaluateView.as_view()),  # Main endpoint?
```

**Issue:** API contract only specifies `POST /api/v1/triage/`. Which one should frontend use?

**Fix:** 
- Make `POST /api/v1/triage/` the main endpoint (integrate M5 + M6)
- Move `/ai/` and `/pdf-extract/` to internal/testing endpoints

### 🟡 Medium Issues:

#### 21. **Member 6's Service Returns Envelope**
**Location:** `triage/services/triage_service.py` line 245  
**Problem:**
```python
return {
    "success": True,  # ❌ Envelope
    "data": {...}
}
```

**API Contract:** No success envelopes

**Fix:** Return direct triage result dict

#### 22. **No Database Persistence in Triage Service**
**Location:** `triage/services/triage_service.py`  
**Problem:** `evaluate_triage()` calculates everything but never saves to database

**Fix:** Either:
- Member 3 saves after calling Member 6 (recommended)
- Member 6 saves to `PatientSubmission`

#### 23. **Triage Models Not Used**
**Location:** `triage/models.py`  
**Problem:** Has `TriageSession`, `AIResult`, `FileUpload` models but **nothing uses them**

**What's Actually Used:** `PatientSubmission` (in patients/models.py)

**Fix:** Either:
- Delete unused models
- Or migrate to use `TriageSession` instead of `PatientSubmission`

#### 24. **AI Service Has Multiple Implementations**
**Location:** `triage/services/ai_service.py`  
**Problem:** Has keyword-based rules, not actual AI calls

**Expected (Member 5):** Call OpenAI/Gemini API

**Current:** Simple keyword matching

**Fix:** Implement actual AI integration or rename to `keyword_service.py`

### 🟢 Minor Issues:

#### 25. **Test Files in Wrong Location**
**Location:** `triage/test_triage.py` (root of app)  
**Should Be:** `triage/tests/test_triage.py` (in tests folder)

#### 26. **Unused Imports in triage_service.py**
**Location:** Multiple unused imports from `triage_config`

---

## 📁 FOLDER 4: DASHBOARD (Member 4)

**Owner:** Member 4  
**Responsibility:** Staff queue, filtering, sorting, Admin stats, analytics

### ✅ What's Good:
- Clean service layer separation
- Good query structure
- Proper serializers

### 🟡 Medium Issues:

#### 27. **No WebSocket Broadcast After Status Update**
**Location:** `dashboard/services/dashboard_service.py` - `update_patient_status()`  
**Problem:** Updates status but doesn't broadcast event

**API Contract:** "WebSocket MUST trigger on: status changed"

**Fix:**
```python
from apps.realtime.services.broadcast_service import broadcast_status_changed

def update_patient_status(patient_id, status):
    patient = PatientSubmission.objects.get(id=patient_id)
    patient.status = status
    patient.save()
    
    # Broadcast event
    broadcast_status_changed(patient_id, status)
    
    return patient
```

#### 28. **No Status Transition Validation**
**Location:** `dashboard/services/dashboard_service.py`  
**Problem:** Can go from `completed` → `waiting` (invalid)

**Fix:** Use Member 6's `validate_status_transition()`:
```python
from apps.triage.services.triage_service import validate_status_transition

if not validate_status_transition(patient.status, new_status):
    raise ValueError("Invalid transition")
```

#### 29. **Missing select_related() for Performance**
**Location:** `dashboard/services/dashboard_service.py` line 11  
**Problem:**
```python
queryset = PatientSubmission.objects.all()  # ❌ N+1 queries
```

**Fix:**
```python
queryset = PatientSubmission.objects.select_related('patient__user').all()
```

### 🟢 Minor Issues:

#### 30. **Inconsistent Error Handling**
**Location:** `dashboard/views.py`  
**Problem:** Some views return `None`, others raise exceptions

**Fix:** Standardize error handling

---

## 📁 FOLDER 5: REALTIME (Member 8)

**Owner:** Member 8  
**Responsibility:** Django Channels, Redis, WebSocket broadcasting

### ✅ What's Good:
- Clean separation: `consumers.py`, `broadcast_service.py`, `event_service.py`
- Good event builder pattern
- Proper async/sync handling

### 🔴 Critical Issues:

#### 31. **Event Names Don't Match API Contract**
**Location:** `realtime/services/event_service.py`  
**Problem:**
```python
"type": "PATIENT_CREATED"  # ❌ Contract says "TRIAGE_CREATED"
"type": "PRIORITY_UPDATE"  # ✅ Correct
"type": "CRITICAL_ALERT"   # ✅ Correct
"type": "STATUS_CHANGED"   # ❌ Contract says "TRIAGE_UPDATED"
```

**API Contract (Section 3.6):**
- `TRIAGE_CREATED` (not PATIENT_CREATED)
- `TRIAGE_UPDATED` (not STATUS_CHANGED)
- `CRITICAL_ALERT` ✅
- `SLA_BREACH` (not implemented)

**Fix:**
```python
def build_patient_created_event(...):
    return _base_event("TRIAGE_CREATED", {...})  # ✅

def build_status_changed_event(...):
    return _base_event("TRIAGE_UPDATED", {...})  # ✅
```

### 🟡 Medium Issues:

#### 32. **Missing WebSocket Routing Configuration**
**Location:** Should be in `realtime/routing.py`  
**Status:** File exists but need to verify it's configured in `config/asgi.py`

### 🟢 Minor Issues:

#### 33. **No WebSocket Authentication**
**Location:** `realtime/consumers.py`  
**Problem:** Comment says "JWT authentication handled by M2" but no middleware exists

**Fix:** Member 2 needs to create WebSocket auth middleware

---

## 📁 FOLDER 6: CORE (Member 1)

**Owner:** Member 1  
**Responsibility:** Standard API response format, Global exception handling, Shared validators, Helper utilities

### 🔴 Critical Issues:

#### 34. **Response Helpers Create Envelopes (Violates Contract)**
**Location:** `core/response.py`  
**Problem:**
```python
def success_response(data=None, message=None, ...):
    response_data = {}
    if message:
        response_data['message'] = message  # ❌ Adds envelope
    if data is not None:
        if isinstance(data, dict):
            response_data.update(data)  # ❌ Wraps data
```

**API Contract (Section 2.3):**
> Success (2xx): direct JSON resources (object/array), **no success envelope**

**Problem:** These helpers are used by Member 2 (auth) and create envelopes

**Fix:** Either:
- **Option A:** Remove these helpers, use direct `Response()`
- **Option B:** Rename to `legacy_success_response()` and create new contract-compliant helpers

### 🟡 Medium Issues:

#### 35. **Error Response Format Wrong**
**Location:** `core/response.py` - `error_response()`  
**Problem:**
```python
response_data = {'error': error}  # ❌ Should be 'code' and 'message'
```

**API Contract:**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "..."
}
```

**Fix:**
```python
def error_response(code, message, details=None, status_code=400):
    response_data = {
        'code': code,
        'message': message
    }
    if details:
        response_data['details'] = details
    return Response(response_data, status=status_code)
```

#### 36. **Missing Validators**
**Location:** `core/` app  
**Problem:** Task Classification says Member 1 owns "Shared validators (length, required fields)"

**Current:** Only has `validate_priority()` and `validate_urgency_score()` in `utils.py`

**Missing:**
- Input length validator (500 chars)
- Required field validator
- Email validator
- Phone validator

**Fix:** Create `core/validators.py` with all shared validators

### 🟢 Minor Issues:

#### 37. **Unused Exception Classes**
**Location:** `core/exceptions.py`  
**Problem:** Defines `TriageException`, `AIServiceException`, etc. but **nothing uses them**

**Fix:** Either use them or remove them

#### 38. **No Logging Configuration**
**Location:** `core/` app  
**Problem:** No centralized logging setup

**Fix:** Create `core/logging.py` with logger configuration

---

## 📊 Architectural Issues Summary

### 🏗️ Major Architectural Problems:

1. **Triage Submission in Wrong App**
   - Main triage endpoint is in `patients/` app
   - Should be in `triage/` app
   - Wrong URL path

2. **Middleware in Wrong App**
   - Payload sanitizer is in `triage/` app
   - Should be in `core/` app

3. **Response Helpers Violate Contract**
   - `core/response.py` creates envelopes
   - API contract forbids envelopes
   - Used by multiple apps

4. **Duplicate/Unused Models**
   - `TriageSession` model exists but unused
   - `PatientSubmission` is actually used
   - Confusion about which model to use

5. **Event Names Don't Match Contract**
   - `PATIENT_CREATED` should be `TRIAGE_CREATED`
   - `STATUS_CHANGED` should be `TRIAGE_UPDATED`

6. **No Integration Between Members**
   - Member 3 calls non-existent functions
   - Member 6's service not called properly
   - Member 8's events not triggered

---

## 🎯 Recommended Refactoring Plan

### Phase 1: Fix Critical Architectural Issues (2-3 hours)
1. Move `PatientTriageView` from `patients/` to `triage/`
2. Fix URL routing to match API contract
3. Remove response envelopes from `core/response.py`
4. Fix event names in `realtime/services/event_service.py`
5. Delete duplicate `triage/url.py`
6. Move `triage/middleware.py` to `core/middleware/`

### Phase 2: Fix Integration Issues (2-3 hours)
7. Fix model references (`TriageItem` → `PatientSubmission`)
8. Integrate Member 6's `evaluate_triage()` properly
9. Add WebSocket broadcasts after status updates
10. Add status transition validation

### Phase 3: Clean Up Code (1-2 hours)
11. Remove unused models or migrate to use them
12. Standardize error responses
13. Add missing validators to `core/`
14. Fix permission classes

### Phase 4: Add Missing Features (2-3 hours)
15. Implement refresh token endpoint
16. Add WebSocket authentication middleware
17. Add patient profile management endpoints
18. Implement missing admin endpoints

---

## 📋 File Movement Checklist

### Files to Move:
- [ ] `triage/middleware.py` → `core/middleware/payload_sanitizer.py`
- [ ] `patients/views.py::PatientTriageView` → `triage/views.py::TriageSubmissionView`
- [ ] `triage/test_triage.py` → `triage/tests/test_triage.py`

### Files to Delete:
- [ ] `triage/url.py` (duplicate)
- [ ] `triage/models.py::TriageSession` (if unused)
- [ ] `triage/models.py::AIResult` (if unused)
- [ ] `triage/models.py::FileUpload` (if unused)

### Files to Create:
- [ ] `authentication/middleware/websocket_auth.py`
- [ ] `authentication/views.py::RefreshTokenView`
- [ ] `patients/services/patient_service.py`
- [ ] `patients/views.py::PatientProfileView`
- [ ] `core/validators.py`
- [ ] `core/logging.py`

---

**Generated:** 2026-04-28  
**Audit Status:** ⚠️ Major Refactoring Required  
**Estimated Fix Time:** 8-12 hours total
