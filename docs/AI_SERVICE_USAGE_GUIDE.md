# AI Service Usage Guide

## Quick Start

The AI service provides intelligent medical triage recommendations using Google's Gemini AI with rule-based fallbacks.

## API Endpoints

### 1. AI Triage Recommendation
**Endpoint**: `POST /api/v1/triage/ai/`  
**Permission**: AllowAny  
**Purpose**: Get AI-powered triage recommendation without creating a submission

**Request**:
```json
{
  "symptoms": "Patient has chest pain and sweating",
  "age": 45,
  "gender": "male"
}
```

**Response** (200 OK):
```json
{
  "priority_level": 1,
  "urgency_score": 95,
  "reason": "Possible heart attack due to chest pain and associated symptoms.",
  "recommended_action": "Immediate ECG and transfer to ER",
  "condition": "Acute Angina Suspicion",
  "category": "Cardiac",
  "is_critical": true,
  "explanation": ["chest pain", "sweating"],
  "source": "ai"
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "error": "AI unavailable, staff review required",
  "message": "Our AI triage service is temporarily unavailable. Your case will be queued for staff review.",
  "details": ["gemini-2.5-flash (attempt 1): Quota exceeded..."],
  "error_types": ["quota"]
}
```

### 2. PDF Triage Extraction
**Endpoint**: `POST /api/v1/triage/pdf/`  
**Permission**: AllowAny  
**Purpose**: Extract text from PDF and get triage recommendation

**Request** (multipart/form-data):
```
file: <PDF file>
age: 45 (optional)
gender: male (optional)
```

**Response**: Same as AI Triage Recommendation

### 3. Main Triage Submission
**Endpoint**: `POST /api/v1/triage/`  
**Permission**: IsAuthenticated, IsPatient  
**Purpose**: Create a triage submission (saves to database)

**Request**:
```json
{
  "description": "Patient has chest pain and sweating",
  "photo_name": "chest_xray.jpg" (optional)
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "description": "Patient has chest pain and sweating",
  "priority": 1,
  "urgency_score": 95,
  "condition": "Acute Angina Suspicion",
  "status": "CRITICAL",
  "photo_name": "chest_xray.jpg",
  "created_at": "2026-04-29T07:40:00Z"
}
```

## Python API

### High-Level Functions

#### 1. Get AI Triage Recommendation
```python
from triagesync_backend.apps.triage.services.ai_service import get_triage_recommendation

result = get_triage_recommendation(
    symptoms="chest pain and sweating",
    age=45,
    gender="male"
)

# Result contains:
# - priority_level (1-5)
# - urgency_score (0-100)
# - condition (string)
# - category (Cardiac|Respiratory|Trauma|Neurological|General)
# - is_critical (boolean)
# - explanation (list of key symptoms)
# - recommended_action (string)
# - reason (string)
```

#### 2. Rule-Based Inference (Fallback)
```python
from triagesync_backend.apps.triage.services.ai_service import infer_priority

result = infer_priority("chest pain")

# Result contains:
# - priority (1-5)
# - urgency_score (0-100)
# - condition (string)
```

#### 3. Complete Triage Evaluation
```python
from triagesync_backend.apps.triage.services.triage_service import evaluate_triage

result = evaluate_triage("chest pain and sweating")

# Result is an envelope:
# {
#   "success": True,
#   "data": {
#     "source": "EMERGENCY_OVERRIDE" | "AI_SYSTEM",
#     "module": "member6_triage_service",
#     "triage_result": {
#       "priority": 1,
#       "urgency_score": 100,
#       "status": "CRITICAL",
#       "is_critical": True
#     },
#     "ai_contract": {...},
#     "staff_view": {...},
#     "admin_view": {...},
#     "system_meta": {...},
#     "event": {...}
#   }
# }
```

### Utility Functions

#### Normalize Demographics
```python
from triagesync_backend.apps.triage.services.ai_service import normalize_age, normalize_gender

age = normalize_age(45)        # Returns: 45
age = normalize_age("45")      # Returns: 45
age = normalize_age(-5)        # Returns: None
age = normalize_age(200)       # Returns: None

gender = normalize_gender("M")           # Returns: "male"
gender = normalize_gender("female")      # Returns: "female"
gender = normalize_gender("nonbinary")   # Returns: "other"
gender = normalize_gender("unknown")     # Returns: "unknown"
```

#### Emergency Override Check
```python
from triagesync_backend.apps.triage.services.triage_service import check_emergency_override

result = check_emergency_override("chest pain")

# If emergency keyword found:
# {
#   "override": True,
#   "matched_keyword": "chest pain",
#   "urgency_score": 100,
#   "condition": "Emergency Override",
#   ...
# }

# If no emergency keyword:
# {
#   "override": False,
#   ...
# }
```

#### Status Transition Validation
```python
from triagesync_backend.apps.triage.services.triage_service import validate_status_transition

# Valid transitions
validate_status_transition("waiting", "in_progress")  # Returns: True
validate_status_transition("waiting", "completed")    # Returns: True
validate_status_transition("in_progress", "completed") # Returns: True

# Invalid transitions
validate_status_transition("completed", "waiting")    # Returns: False
validate_status_transition("completed", "in_progress") # Returns: False
```

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
GEMINI_MODEL_PRIORITY=["gemini-2.5-flash", "gemini-1.5-flash"]
GEMINI_MAX_RETRIES=2
GEMINI_TIMEOUT_SECONDS=8
GEMINI_CIRCUIT_BREAKER_THRESHOLD=5
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS=30
GEMINI_MODEL_LIST_TTL_SECONDS=600
```

### Django Settings

```python
# settings.py

# Gemini API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_PRIORITY = ["gemini-2.5-flash", "gemini-1.5-flash"]
GEMINI_MAX_RETRIES = 2
GEMINI_TIMEOUT_SECONDS = 8
GEMINI_CIRCUIT_BREAKER_THRESHOLD = 5
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 30
GEMINI_MODEL_LIST_TTL_SECONDS = 600

# Triage Configuration
PRIORITY_THRESHOLDS = {
    "critical": 80,  # Priority 1
    "high": 60,      # Priority 2
    "medium": 40,    # Priority 3
    "low": 20,       # Priority 4
                     # Priority 5 (< 20)
}

TRIAGE_FALLBACK = {
    "priority": 3,
    "urgency_score": 50,
    "condition": "Unknown - Staff Review Required"
}
```

## Emergency Keywords

The following keywords trigger immediate priority 1 override:

1. chest pain
2. no breathing
3. not breathing
4. unconscious
5. unresponsive
6. severe bleeding
7. heart attack
8. stroke
9. seizure
10. cardiac arrest

## Priority Levels

| Priority | Urgency Score | Description | Example |
|----------|---------------|-------------|---------|
| 1 | 80-100 | Immediate/Life-threatening | Cardiac arrest, severe bleeding |
| 2 | 60-79 | Emergent | Chest pain, stroke symptoms |
| 3 | 40-59 | Urgent | High fever, moderate pain |
| 4 | 20-39 | Semi-urgent | Minor fracture, mild dehydration |
| 5 | 0-19 | Non-urgent | Mild cough, minor rash |

## Categories

- **Cardiac**: Heart-related conditions
- **Respiratory**: Breathing and lung issues
- **Trauma**: Injuries and physical trauma
- **Neurological**: Brain and nervous system
- **General**: Other conditions

## Error Handling

### Circuit Breaker

The circuit breaker protects against API quota exhaustion:

- **Threshold**: 5 consecutive failures
- **Cooldown**: 30 seconds
- **Behavior**: Automatically switches to rule-based fallback

```python
from triagesync_backend.apps.triage.services.ai_service import reset_circuit_breaker

# Reset circuit breaker (for testing/ops)
reset_circuit_breaker()
```

### Model Fallback

The system tries models in priority order:

1. **gemini-2.5-flash** (primary)
2. **gemini-1.5-flash** (secondary)
3. **Rule-based inference** (tertiary)

### Cache Management

```python
from triagesync_backend.apps.triage.services.ai_service import invalidate_model_list_cache

# Force refresh of model list cache
invalidate_model_list_cache()
```

## Testing

### Run Comprehensive Tests

```bash
cd Django-Backend
python test_ai_service_complete.py
```

### Run Django Tests

```bash
cd Django-Backend
python manage.py test triagesync_backend.apps.triage.tests
```

### Test Specific Function

```python
from triagesync_backend.apps.triage.services.ai_service import get_triage_recommendation

# Test with emergency symptoms
result = get_triage_recommendation("chest pain and sweating", age=45, gender="male")
print(f"Priority: {result['priority_level']}")
print(f"Urgency: {result['urgency_score']}")
print(f"Condition: {result['condition']}")
print(f"Critical: {result['is_critical']}")

# Test with mild symptoms
result = get_triage_recommendation("mild headache", age=25, gender="female")
print(f"Priority: {result['priority_level']}")
print(f"Urgency: {result['urgency_score']}")
```

## Best Practices

### 1. Input Validation

Always validate and sanitize user input:

```python
from triagesync_backend.apps.core.validators import validate_description_length
from django.core.exceptions import ValidationError

try:
    validate_description_length(description)
except ValidationError as e:
    # Handle validation error
    return error_response("VALIDATION_ERROR", str(e))
```

### 2. Error Handling

Handle AI unavailability gracefully:

```python
result = get_triage_recommendation(symptoms, age, gender)

if isinstance(result, dict) and "error" in result:
    # AI unavailable - queue for staff review
    return Response({
        "error": "AI unavailable, staff review required",
        "message": result.get("error"),
        "details": result.get("details", [])
    }, status=503)
```

### 3. Logging

Use structured logging for debugging:

```python
import logging

logger = logging.getLogger("triage.ai")
logger.info(f"Triage request for user {user_id}")
logger.warning(f"AI unavailable: {error_details}")
logger.error(f"Triage failed: {exception}")
```

### 4. Demographics

Always normalize demographics before passing to AI:

```python
from triagesync_backend.apps.triage.services.ai_service import normalize_age, normalize_gender

age = normalize_age(request.data.get("age"))
gender = normalize_gender(request.data.get("gender"))

result = get_triage_recommendation(symptoms, age=age, gender=gender)
```

## Troubleshooting

### Issue: "AI unavailable, staff review required"

**Possible Causes**:
1. Gemini API quota exceeded
2. Network connectivity issues
3. Invalid API key
4. Circuit breaker open

**Solutions**:
1. Check API quota in Google Cloud Console
2. Verify network connectivity
3. Verify GEMINI_API_KEY in .env file
4. Wait for circuit breaker cooldown (30s) or reset manually

### Issue: "Timeout after 8s"

**Possible Causes**:
1. Slow API response
2. Network latency

**Solutions**:
1. Increase GEMINI_TIMEOUT_SECONDS in settings
2. Check network connectivity
3. Try different model (gemini-1.5-flash is faster)

### Issue: "Model not found or not enabled"

**Possible Causes**:
1. Model not enabled for API key
2. Model name incorrect

**Solutions**:
1. Enable models in Google Cloud Console
2. Verify model names in GEMINI_MODEL_PRIORITY
3. Check available models with `genai.list_models()`

## Support

For issues or questions:
1. Check logs: `Django-Backend/logs/`
2. Run diagnostic test: `python test_ai_service_complete.py`
3. Review error details in API response
4. Check circuit breaker status

---

**Last Updated**: April 29, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
