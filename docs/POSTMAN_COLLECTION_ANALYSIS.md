# Postman Collection Analysis - Triage Endpoint Testing

## Context

Debug logging was recently added to `Django-Backend/triagesync_backend/apps/triage/views.py` to diagnose validation issues with the authenticated triage submission endpoint.

## Current State

### Existing Postman Tests

The current Postman collection (`.postman.json`) includes:
- ✅ Authentication endpoints (login for patient and staff)
- ✅ Patient profile endpoints
- ✅ Patient history endpoints
- ✅ **Triage AI endpoint** (`POST /api/v1/triage/ai/`) - 10 test cases
- ❌ **Missing: Authenticated triage submission endpoint** (`POST /api/v1/triage/`)

### API Endpoint Comparison

There are **two different triage endpoints** with different requirements:

| Endpoint | Authentication | Field Name | Purpose |
|----------|---------------|------------|---------|
| `/api/v1/triage/ai/` | ❌ Not required | `symptoms` | AI analysis only, no database storage |
| `/api/v1/triage/` | ✅ Required (Patient token) | `description` | Full triage submission with database storage |

## Issues Identified

### 1. Missing Test Coverage

The Postman collection does **not test** the authenticated triage submission endpoint (`POST /api/v1/triage/`), which is the endpoint that:
- Requires JWT authentication
- Uses the `description` field (not `symptoms`)
- Creates a database record
- Triggers notifications
- Returns a full submission object with ID

### 2. Field Name Confusion

The debug logging was added because the endpoint expects `description` but may be receiving:
- Empty requests
- Requests with `symptoms` instead of `description`
- Malformed JSON

### 3. Debug Logging Added

The following debug logs were added to diagnose the issue:

```python
# DEBUG: Log the incoming request data
logger.info(f"Request data: {request.data}")
logger.info(f"Request content type: {request.content_type}")

# DEBUG: Log what we extracted
logger.info(f"Extracted description: {description}")
logger.info(f"Description type: {type(description)}")
logger.info(f"Description bool: {bool(description)}")

# Validation failure logging
if not description:
    logger.error(f"Description validation failed. Request data was: {request.data}")
```

## Proposed Fixes

### Fix 1: Add Authenticated Triage Submission Tests

Add the following test cases to the Postman collection under a new section "Triage Submission Endpoints":

#### Test Cases Needed:

1. **POST /api/v1/triage/ - Successful Submission**
   - Use patient token
   - Send `{"description": "chest pain and shortness of breath"}`
   - Expect 200 OK with submission ID, priority, urgency_score, condition, status

2. **POST /api/v1/triage/ - Missing Description (400)**
   - Use patient token
   - Send `{}` or `{"photo_name": "test.jpg"}`
   - Expect 400 with validation error

3. **POST /api/v1/triage/ - Description Too Long (400)**
   - Use patient token
   - Send description > 500 characters
   - Expect 400 with validation error

4. **POST /api/v1/triage/ - Unauthorized (401)**
   - No token
   - Send valid description
   - Expect 401 unauthorized

5. **POST /api/v1/triage/ - Forbidden (403)**
   - Use staff token (not patient)
   - Send valid description
   - Expect 403 forbidden

6. **POST /api/v1/triage/ - With Photo Name**
   - Use patient token
   - Send `{"description": "severe headache", "photo_name": "headache_photo.jpg"}`
   - Expect 200 OK with photo_name in response

### Fix 2: Update API Documentation

The API documentation should clearly distinguish between:
- `/api/v1/triage/ai/` - uses `symptoms` field, no auth required
- `/api/v1/triage/` - uses `description` field, patient auth required

### Fix 3: Consider Field Name Standardization (Future)

For consistency, consider:
- Option A: Accept both `symptoms` and `description` as aliases
- Option B: Standardize on one field name across both endpoints
- Option C: Keep separate (current approach) but document clearly

## Recommended Actions

1. **Immediate**: Add the 6 missing test cases to the Postman collection
2. **Short-term**: Run the updated collection to verify the endpoint works correctly
3. **Medium-term**: Remove debug logging once issue is resolved
4. **Long-term**: Consider field name standardization for better developer experience

## Test Data Requirements

To run the tests, ensure:
- ✅ Test users exist in database:
  - `patient_test` with password `testpass123` (role: patient)
  - `staff_test` with password `testpass123` (role: staff/doctor/nurse)
- ✅ Django server is running on `http://localhost:8000`
- ✅ Database is accessible and migrations are applied
- ✅ Gemini API key is configured (for AI triage evaluation)

## Example Test Request

```bash
# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "patient_test", "password": "testpass123"}'

# Submit triage (use token from login response)
curl -X POST http://localhost:8000/api/v1/triage/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"description": "chest pain and difficulty breathing"}'
```

## Expected Response

```json
{
  "id": 123,
  "description": "chest pain and difficulty breathing",
  "priority": 1,
  "urgency_score": 95,
  "condition": "Acute Cardiac Event",
  "status": "waiting",
  "photo_name": null,
  "created_at": "2026-05-01T10:30:00Z",
  "patient": 1
}
```

## Conclusion

The Postman collection is missing critical test coverage for the authenticated triage submission endpoint. The debug logging was added to diagnose why this endpoint might be failing, likely due to:
- Missing `description` field in requests
- Using `symptoms` instead of `description`
- Authentication issues

Adding the proposed test cases will provide comprehensive coverage and help identify the root cause of any validation failures.
