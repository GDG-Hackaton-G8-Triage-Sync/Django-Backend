# 🚀 Comprehensive Integration & Refactoring Plan

**Date:** 2026-04-28  
**Branch:** feature/AI_service  
**Status:** Ready for Implementation

---

## 📊 Situation Analysis

After reviewing both the **Integration Review** and **Folder Audit Report**, here's the consolidated picture:

### Issues Found:
- **Integration Issues:** 25
- **Architectural Issues:** 38
- **Total Unique Issues:** 45 (some overlap)

### Severity Breakdown:
- 🔴 **Critical (Must Fix):** 15 issues
- 🟡 **High Priority:** 18 issues
- 🟢 **Medium Priority:** 12 issues

### Root Causes:
1. **Lack of Integration Testing** - Members built in isolation
2. **No Architectural Review** - Code placed in wrong apps
3. **API Contract Not Enforced** - Response formats don't match
4. **Incomplete Task Handoffs** - Member 3 calls Member 6's non-existent functions

---

## 🎯 Strategic Approach

### Philosophy:
**"Fix the foundation first, then build up"**

We'll fix issues in this order:
1. **Architectural** (move files to correct locations)
2. **Integration** (connect the pieces)
3. **Contract Compliance** (match API contract)
4. **Polish** (performance, logging, etc.)

---

## 📋 Phase 1: Architectural Fixes (2-3 hours)

**Goal:** Put code in the right places according to task classification

### 1.1 Move Triage Submission Endpoint ⚡ CRITICAL

**Problem:** Main triage endpoint is in `patients/` app, should be in `triage/`

**Actions:**
```bash
# 1. Create new proper triage submission view in triage/views.py
# 2. Delete PatientTriageView from patients/views.py
# 3. Update triage/urls.py to mount at correct path
# 4. Update patients/urls.py to remove triage routes
```

**New Structure:**
```python
# triage/views.py
class TriageSubmissionView(APIView):
    """POST /api/v1/triage/ - Main triage submission endpoint"""
    permission_classes = [IsAuthenticated, IsPatient]
    
    def post(self, request):
        # 1. Validate input
        # 2. Call Member 6's evaluate_triage()
        # 3. Save to PatientSubmission
        # 4. Broadcast event
        # 5. Return direct TriageItem shape
        pass

# triage/urls.py
urlpatterns = [
    path("", TriageSubmissionView.as_view(), name='triage-submit'),  # ✅ /api/v1/triage/
    path('ai/', TriageAIView.as_view(), name='triage-ai'),
    path('pdf-extract/', TriagePDFExtractView.as_view(), name='triage-pdf-extract'),
]
```

**Impact:** Fixes 5 issues (#3, #8, #9, #10, #11 from reports)

---

### 1.2 Move Middleware to Core ⚡ CRITICAL

**Problem:** `triage/middleware.py` is request sanitization, should be in `core/`

**Actions:**
```bash
# 1. Move file
mv triagesync_backend/apps/triage/middleware.py \
   triagesync_backend/apps/core/middleware/payload_sanitizer.py

# 2. Update imports in settings.py
# 3. Update any references
```

**Rationale:**
- Task Classification: Member 1 (Core) owns "Shared validators"
- Middleware that runs on ALL requests belongs in `core/`
- Not triage-specific logic

**Impact:** Fixes issue #18

---

### 1.3 Delete Duplicate Files ⚡ CRITICAL

**Problem:** `triage/url.py` and `triage/urls.py` both exist

**Actions:**
```bash
# Delete the old one
rm triagesync_backend/apps/triage/url.py
```

**Impact:** Fixes issue #17

---

### 1.4 Fix Core Response Helpers ⚡ CRITICAL

**Problem:** `core/response.py` creates envelopes, violating API contract

**Decision Point:** Two options:

**Option A: Remove Envelopes (Recommended)**
```python
# core/response.py
def success_response(data, status_code=200):
    """Return direct data, no envelope"""
    return Response(data, status=status_code)

def error_response(code, message, details=None, status_code=400):
    """Return {code, message, details} format"""
    response_data = {"code": code, "message": message}
    if details:
        response_data["details"] = details
    return Response(response_data, status=status_code)
```

**Option B: Create New Helpers, Deprecate Old**
```python
# core/response.py

# NEW - Contract compliant
def direct_response(data, status_code=200):
    return Response(data, status=status_code)

def contract_error(code, message, details=None, status_code=400):
    return Response({"code": code, "message": message, "details": details}, status=status_code)

# OLD - Deprecated (for backward compatibility)
def success_response(...):  # Keep for now, mark deprecated
    pass
```

**Recommendation:** Option A - Clean break, fix all usages

**Impact:** Fixes issues #1, #2, #6, #34, #35

---

## 📋 Phase 2: Integration Fixes (3-4 hours)

**Goal:** Connect Member 3 → Member 6 → Member 8 properly

### 2.1 Create Proper Triage Submission Flow ⚡ CRITICAL

**File:** `triage/views.py` - New `TriageSubmissionView`

**Implementation:**
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.authentication.permissions import IsPatient
from apps.patients.models import Patient, PatientSubmission
from apps.triage.services.triage_service import evaluate_triage
from apps.realtime.services.broadcast_service import broadcast_patient_created


class TriageSubmissionView(APIView):
    """
    POST /api/v1/triage/
    Main triage submission endpoint (Member 3 + Member 6 + Member 8 integration)
    """
    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request):
        # 1. Get description from request (API contract field name)
        description = request.data.get("description")
        photo_name = request.data.get("photo_name")
        
        if not description:
            return Response({
                "code": "VALIDATION_ERROR",
                "message": "Description is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Validate length (500 chars max)
        if len(description) > 500:
            return Response({
                "code": "VALIDATION_ERROR",
                "message": "Description cannot exceed 500 characters"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 3. Get or create Patient profile
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            patient = Patient.objects.create(
                user=request.user,
                name=request.user.username
            )
        
        # 4. Call Member 6's triage service
        triage_result = evaluate_triage(description)
        
        # Extract data from Member 6's response
        triage_data = triage_result["data"]["triage_result"]
        priority = triage_data["priority"]
        urgency_score = triage_data["urgency_score"]
        condition = triage_data["condition"]
        status_value = triage_data["status"]
        
        # 5. Save to database (Member 7's model)
        submission = PatientSubmission.objects.create(
            patient=patient,
            symptoms=description,  # Model field is still "symptoms"
            photo_name=photo_name,
            priority=priority,
            urgency_score=urgency_score,
            condition=condition,
            status=status_value
        )
        
        # 6. Broadcast WebSocket event (Member 8)
        broadcast_patient_created(
            patient_id=submission.id,
            priority=priority,
            urgency_score=urgency_score
        )
        
        # 7. Return direct TriageItem shape (no envelope)
        return Response({
            "id": submission.id,
            "description": description,  # API contract field name
            "priority": priority,
            "urgency_score": urgency_score,
            "condition": condition,
            "status": status_value,
            "created_at": submission.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)
```

**Impact:** Fixes issues #2, #4, #5, #6, #7, #8, #9, #10, #11

---

### 2.2 Fix Member 6's Service Response Format

**File:** `triage/services/triage_service.py`

**Problem:** Returns `{"success": True, "data": {...}}` envelope

**Fix:**
```python
# Option A: Change evaluate_triage() to return direct dict
def evaluate_triage(symptoms: str) -> dict:
    # ... existing logic ...
    
    # Return direct triage result (no envelope)
    return {
        "priority": result["priority"],
        "urgency_score": result["urgency_score"],
        "condition": result["condition"],
        "status": result["status"],
        "is_critical": result["is_critical"]
    }

# Option B: Keep internal format, extract in view (current approach)
# View extracts: triage_result["data"]["triage_result"]
```

**Recommendation:** Option B (less breaking changes for now)

**Impact:** Fixes issue #21

---

### 2.3 Add WebSocket Broadcasts After Status Updates

**File:** `dashboard/services/dashboard_service.py`

**Fix:**
```python
from apps.realtime.services.broadcast_service import broadcast_status_changed
from apps.triage.services.triage_service import validate_status_transition

def update_patient_status(patient_id, new_status):
    """Update workflow status with validation and broadcast"""
    try:
        patient = PatientSubmission.objects.get(id=patient_id)
        
        # Validate transition (Member 6's logic)
        if not validate_status_transition(patient.status, new_status):
            raise ValueError(f"Invalid transition: {patient.status} -> {new_status}")
        
        # Update status
        patient.status = new_status
        patient.save()
        
        # Broadcast event (Member 8)
        broadcast_status_changed(patient_id, new_status)
        
        return patient
    except PatientSubmission.DoesNotExist:
        return None
```

**Impact:** Fixes issues #16, #27, #28

---

### 2.4 Fix WebSocket Event Names

**File:** `realtime/services/event_service.py`

**Fix:**
```python
def build_patient_created_event(patient_id: int, priority: int, urgency_score: int) -> dict:
    """Triggered when a new patient submission is created."""
    return _base_event(
        "TRIAGE_CREATED",  # ✅ Changed from PATIENT_CREATED
        {
            "id": patient_id,
            "priority": priority,
            "urgency_score": urgency_score,
        },
    )

def build_status_changed_event(patient_id: int, status: str) -> dict:
    """Triggered when staff updates a patient status."""
    return _base_event(
        "TRIAGE_UPDATED",  # ✅ Changed from STATUS_CHANGED
        {
            "id": patient_id,
            "status": status,
        },
    )
```

**Impact:** Fixes issues #8, #31

---

## 📋 Phase 3: API Contract Compliance (2-3 hours)

**Goal:** Match all responses to API contract exactly

### 3.1 Fix Authentication Responses

**File:** `authentication/views.py`

**Current:**
```python
return success_response({
    "user": serializer.data,
    "tokens": tokens
})
```

**Fix:**
```python
# RegisterView
return Response({
    "access_token": tokens['access'],
    "refresh_token": tokens['refresh'],
    "role": user.role,
    "user_id": user.id,
    "name": user.username,
    "email": user.email
}, status=status.HTTP_201_CREATED)

# LoginView
return Response({
    "access_token": tokens['access'],
    "refresh_token": tokens['refresh'],
    "role": user.role,
    "user_id": user.id,
    "name": user.username,
    "email": user.email
})
```

**Impact:** Fixes issue #1

---

### 3.2 Add Missing Refresh Token Endpoint

**File:** `authentication/views.py`

**Add:**
```python
from rest_framework_simplejwt.views import TokenRefreshView

class RefreshTokenView(TokenRefreshView):
    """POST /api/v1/auth/refresh/"""
    pass
```

**File:** `authentication/urls.py`

**Add:**
```python
path('refresh/', RefreshTokenView.as_view(), name='token-refresh'),
```

**Impact:** Fixes issue #3

---

### 3.3 Fix Dashboard Serializer Field Names

**File:** `dashboard/serializers.py`

**Current:**
```python
description = serializers.CharField(source="symptoms")  # ✅ Already correct
```

**Verify:** This is already correct - maps model's "symptoms" to API's "description"

---

### 3.4 Add Missing Endpoints

**Files to Create:**

1. **`patients/views.py` - Patient Profile Management**
```python
class PatientProfileView(APIView):
    """GET/PATCH /api/v1/patients/profile/"""
    permission_classes = [IsAuthenticated, IsPatient]
    
    def get(self, request):
        # Return patient profile
        pass
    
    def patch(self, request):
        # Update patient profile
        pass

class PatientHistoryView(APIView):
    """GET /api/v1/patients/history/"""
    permission_classes = [IsAuthenticated, IsPatient]
    
    def get(self, request):
        # Return patient's triage history
        pass
```

2. **`triage/views.py` - Triage History**
```python
class TriageSubmissionsListView(APIView):
    """GET /api/v1/triage-submissions/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        email = request.query_params.get('email')
        
        # Patient role: always scoped to self
        if request.user.role == 'patient':
            submissions = PatientSubmission.objects.filter(
                patient__user=request.user
            ).order_by('-created_at')
        # Staff/admin: can filter by email
        else:
            if email:
                submissions = PatientSubmission.objects.filter(
                    patient__user__email=email
                ).order_by('-created_at')
            else:
                submissions = PatientSubmission.objects.all().order_by('-created_at')
        
        serializer = DashboardPatientSerializer(submissions, many=True)
        return Response(serializer.data)
```

**Impact:** Fixes issues #12, #13, #20

---

## 📋 Phase 4: Model & Database Fixes (1-2 hours)

**Goal:** Clean up model confusion

### 4.1 Decision: Which Model to Use?

**Current Situation:**
- `TriageSession` (triage/models.py) - Exists but unused
- `PatientSubmission` (patients/models.py) - Actually used everywhere

**Options:**

**Option A: Keep PatientSubmission (Recommended)**
- ✅ Already used everywhere
- ✅ Has all required fields
- ✅ Less breaking changes
- ❌ Name doesn't match API contract ("TriageItem")

**Option B: Migrate to TriageSession**
- ✅ Better name
- ❌ Requires migrating all code
- ❌ Missing some fields

**Option C: Create TriageItem as Proxy**
```python
# patients/models.py
class TriageItem(PatientSubmission):
    class Meta:
        proxy = True
```

**Recommendation:** Option A - Keep `PatientSubmission`, add comment explaining it's the "TriageItem" from API contract

---

### 4.2 Delete Unused Models

**File:** `triage/models.py`

**Action:**
```python
# Delete or comment out:
# - TriageSession (if not used)
# - AIResult (if not used)
# - FileUpload (if not used)

# Or add comment:
# NOTE: These models are for future features (file uploads, session tracking)
# Current implementation uses PatientSubmission from patients app
```

**Impact:** Fixes issue #23

---

## 📋 Phase 5: Performance & Quality (1-2 hours)

**Goal:** Optimize queries and add missing features

### 5.1 Add select_related() to Dashboard Queries

**File:** `dashboard/services/dashboard_service.py`

**Fix:**
```python
def get_patient_queue(priority=None, status=None):
    queryset = PatientSubmission.objects.select_related(
        'patient__user'
    ).all()
    
    if priority:
        queryset = queryset.filter(priority=priority)
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset.order_by("-urgency_score")
```

**Impact:** Fixes issue #29

---

### 5.2 Add Logging

**File:** Create `core/logging.py`

```python
import logging

def get_logger(name):
    """Get configured logger for module"""
    logger = logging.getLogger(name)
    return logger
```

**Usage in views:**
```python
import logging
logger = logging.getLogger(__name__)

def post(self, request):
    logger.info(f"Triage submission from user {request.user.id}")
    # ... rest of code
```

**Impact:** Fixes issue #22

---

### 5.3 Add Missing Validators

**File:** Create `core/validators.py`

```python
from rest_framework import serializers

def validate_description_length(value):
    """Validate description is <= 500 chars"""
    if len(value) > 500:
        raise serializers.ValidationError(
            "Description cannot exceed 500 characters"
        )
    return value

def validate_priority(value):
    """Validate priority is 1-5"""
    if not (1 <= value <= 5):
        raise serializers.ValidationError(
            "Priority must be between 1 and 5"
        )
    return value

def validate_urgency_score(value):
    """Validate urgency score is 0-100"""
    if not (0 <= value <= 100):
        raise serializers.ValidationError(
            "Urgency score must be between 0 and 100"
        )
    return value
```

**Impact:** Fixes issue #36

---

## 📋 Phase 6: Testing & Verification (2-3 hours)

**Goal:** Ensure everything works end-to-end

### 6.1 Manual Testing Checklist

**Test Flow 1: Patient Submission**
```bash
# 1. Register patient
POST /api/v1/auth/register/
{
  "username": "patient1",
  "password": "test123",
  "role": "patient"
}

# 2. Login
POST /api/v1/auth/login/
{
  "username": "patient1",
  "password": "test123"
}

# 3. Submit triage
POST /api/v1/triage/
Authorization: Bearer <token>
{
  "description": "Chest pain and sweating"
}

# Expected: 201 Created with direct TriageItem shape
# Expected: WebSocket event TRIAGE_CREATED broadcast
```

**Test Flow 2: Staff Dashboard**
```bash
# 1. Login as staff
POST /api/v1/auth/login/
{
  "username": "staff1",
  "password": "test123"
}

# 2. Get patient queue
GET /api/v1/dashboard/staff/patients/
Authorization: Bearer <token>

# Expected: Array of patients sorted by urgency_score DESC

# 3. Update status
PATCH /api/v1/dashboard/staff/patient/1/status/
Authorization: Bearer <token>
{
  "status": "in_progress"
}

# Expected: Status updated
# Expected: WebSocket event TRIAGE_UPDATED broadcast
```

**Test Flow 3: WebSocket**
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/triage/events/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type);  // Should be TRIAGE_CREATED, TRIAGE_UPDATED, CRITICAL_ALERT
};
```

---

### 6.2 Automated Testing

**Create:** `triage/tests/test_integration.py`

```python
from django.test import TestCase
from rest_framework.test import APIClient
from apps.authentication.models import User
from apps.patients.models import Patient, PatientSubmission

class TriageIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = User.objects.create_user(
            username='patient1',
            password='test123',
            role='patient'
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            name='Patient One'
        )
    
    def test_full_triage_flow(self):
        """Test complete flow: submit -> triage -> save -> broadcast"""
        # Login
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'patient1',
            'password': 'test123'
        })
        token = response.data['access_token']
        
        # Submit triage
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/api/v1/triage/', {
            'description': 'Chest pain'
        })
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.data)
        self.assertIn('priority', response.data)
        self.assertIn('urgency_score', response.data)
        self.assertEqual(response.data['description'], 'Chest pain')
        
        # Verify saved to database
        submission = PatientSubmission.objects.get(id=response.data['id'])
        self.assertEqual(submission.symptoms, 'Chest pain')
        self.assertIsNotNone(submission.priority)
```

---

## 📊 Implementation Timeline

### Week 1: Critical Fixes
- **Day 1-2:** Phase 1 (Architectural fixes)
- **Day 3-4:** Phase 2 (Integration fixes)
- **Day 5:** Phase 3 (API contract compliance)

### Week 2: Quality & Testing
- **Day 1:** Phase 4 (Model cleanup)
- **Day 2:** Phase 5 (Performance & quality)
- **Day 3-4:** Phase 6 (Testing)
- **Day 5:** Bug fixes & polish

---

## 🎯 Success Criteria

### Must Have (Before Merge):
- [ ] All 15 critical issues fixed
- [ ] Main triage flow works end-to-end
- [ ] API responses match contract exactly
- [ ] WebSocket events broadcast correctly
- [ ] No broken imports or missing functions

### Should Have (Before Production):
- [ ] All 18 high-priority issues fixed
- [ ] Performance optimized (select_related)
- [ ] Logging added
- [ ] Integration tests passing

### Nice to Have (Future):
- [ ] All 12 medium-priority issues fixed
- [ ] Complete test coverage
- [ ] API documentation
- [ ] Rate limiting

---

## 🚨 Risk Mitigation

### Risks:
1. **Breaking existing code** - Many files need changes
2. **Merge conflicts** - Other members may be working
3. **Database migrations** - Model changes need migrations
4. **WebSocket testing** - Hard to test without frontend

### Mitigation:
1. **Create feature branch** - `feature/integration-fixes`
2. **Fix in phases** - Test after each phase
3. **Keep old code** - Comment out, don't delete immediately
4. **Document changes** - Update README with changes
5. **Coordinate with team** - Announce changes in advance

---

## 📝 Communication Plan

### Before Starting:
- [ ] Share this plan with all team members
- [ ] Get approval from tech lead
- [ ] Announce in team chat: "Starting integration fixes"

### During Implementation:
- [ ] Daily updates on progress
- [ ] Flag any blockers immediately
- [ ] Ask for help when stuck

### After Completion:
- [ ] Demo the working flow
- [ ] Update documentation
- [ ] Create PR with detailed description
- [ ] Request code review

---

## 🎓 Lessons Learned

### What Went Wrong:
1. **No integration testing** during development
2. **No architectural review** before coding
3. **API contract not enforced** with validation
4. **Members worked in silos** without communication

### How to Prevent:
1. **Daily standups** - Share what you're building
2. **Code reviews** - Catch issues early
3. **Integration tests** - Test member handoffs
4. **API contract validation** - Automated checks
5. **Shared models** - Agree on data structures first

---

**Generated:** 2026-04-28  
**Status:** ✅ Ready for Implementation  
**Estimated Total Time:** 12-15 hours  
**Priority:** 🔴 Critical - Required for MVP
