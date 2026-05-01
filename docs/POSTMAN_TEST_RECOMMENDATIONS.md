# Postman Collection Test Recommendations

## Summary

Debug logging was added to `Django-Backend/triagesync_backend/apps/triage/views.py` to diagnose validation issues with the authenticated triage submission endpoint. Analysis reveals the Postman collection is missing critical test coverage.

## Key Findings

### 1. Two Different Triage Endpoints

| Endpoint | Auth Required | Field Name | Tests in Collection |
|----------|--------------|------------|---------------------|
| `/api/v1/triage/ai/` | ❌ No | `symptoms` | ✅ 10 tests |
| `/api/v1/triage/` | ✅ Yes (Patient) | `description` | ❌ **0 tests** |

### 2. Missing Test Coverage

The authenticated triage submission endpoint (`POST /api/v1/triage/`) has **zero test coverage** in the Postman collection. This is the endpoint that:
- Requires JWT authentication with patient role
- Uses `description` field (not `symptoms`)
- Creates database records
- Triggers notifications
- Returns full submission objects

### 3. Debug Logging Purpose

The debug logging was added to diagnose why the endpoint might be failing:

```python
logger.info(f"Request data: {request.data}")
logger.info(f"Extracted description: {description}")
logger.info(f"Description type: {type(description)}")

if not description:
    logger.error(f"Description validation failed. Request data was: {request.data}")
```

This suggests the endpoint is receiving:
- Empty requests
- Requests with wrong field name (`symptoms` instead of `description`)
- Malformed JSON

## Recommended Actions

### Immediate: Add Missing Tests

Create a new section in the Postman collection called "Triage Submission Endpoints (Authenticated)" with these 6 tests:

#### 1. Successful Submission
```json
POST /api/v1/triage/
Headers: Authorization: Bearer {{patient_access_token}}
Body: {"description": "chest pain and shortness of breath"}
Expected: 200 OK with id, priority, urgency_score, condition, status
```

#### 2. Missing Description (400)
```json
POST /api/v1/triage/
Headers: Authorization: Bearer {{patient_access_token}}
Body: {}
Expected: 400 with VALIDATION_ERROR
```

#### 3. Description Too Long (400)
```json
POST /api/v1/triage/
Headers: Authorization: Bearer {{patient_access_token}}
Body: {"description": "<501+ characters>"}
Expected: 400 with validation error
```

#### 4. Unauthorized (401)
```json
POST /api/v1/triage/
Headers: (no auth header)
Body: {"description": "test"}
Expected: 401 Unauthorized
```

#### 5. Forbidden - Staff Token (403)
```json
POST /api/v1/triage/
Headers: Authorization: Bearer {{staff_access_token}}
Body: {"description": "test"}
Expected: 403 Forbidden
```

#### 6. With Photo Name
```json
POST /api/v1/triage/
Headers: Authorization: Bearer {{patient_access_token}}
Body: {"description": "severe headache", "photo_name": "photo.jpg"}
Expected: 200 OK with photo_name in response
```

### Short-term: Run Tests

1. Ensure test users exist:
   - `patient_test` / `testpass123` (role: patient)
   - `staff_test` / `testpass123` (role: staff)

2. Start Django server: `python manage.py runserver`

3. Run Postman collection

4. Review debug logs to identify root cause

### Medium-term: Remove Debug Logging

Once the issue is resolved and tests are passing, remove the debug logging statements from the views.

### Long-term: API Consistency

Consider standardizing field names across endpoints:
- **Option A**: Accept both `symptoms` and `description` as aliases
- **Option B**: Use `description` for both endpoints
- **Option C**: Use `symptoms` for both endpoints
- **Current**: Keep separate (document clearly)

## Test Prerequisites

- ✅ PostgreSQL database running
- ✅ Migrations applied
- ✅ Test users created
- ✅ Gemini API key configured
- ✅ Django server running on localhost:8000

## Manual Test Command

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "patient_test", "password": "testpass123"}'

# 2. Submit triage (use access token from step 1)
curl -X POST http://localhost:8000/api/v1/triage/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"description": "chest pain and difficulty breathing"}'
```

## Expected Response Format

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

## Next Steps

1. **Review** this analysis with the team
2. **Add** the 6 missing test cases to Postman collection
3. **Run** the updated collection
4. **Analyze** debug logs to identify root cause
5. **Fix** any issues found
6. **Remove** debug logging once resolved
7. **Document** the field name differences in API docs

## Related Files

- `Django-Backend/triagesync_backend/apps/triage/views.py` - Contains debug logging
- `Django-Backend/.postman.json` - Postman collection (needs updates)
- `Django-Backend/POSTMAN_COLLECTION_ANALYSIS.md` - Detailed analysis
- `Django-Backend/API_DOCUMENTATION.md` - API documentation (needs clarification)

## Contact

If you have questions about this analysis or need help implementing the recommendations, please reach out to the development team.

---

**Generated**: May 1, 2026  
**Status**: Action Required  
**Priority**: High (Missing test coverage for critical endpoint)
