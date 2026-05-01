# Bug Condition Exploration Results

**Date**: 2024-04-29  
**Task**: Task 1 - Write bug condition exploration tests  
**Status**: ✅ COMPLETE - All tests fail as expected, confirming bugs exist

## Summary

Successfully wrote and executed bug condition exploration tests for 3 bugs in the test-suite-failures-fix bugfix spec. All tests **FAILED AS EXPECTED** on the unfixed code, which confirms the bugs exist and validates our root cause analysis.

## Test Results

### Test File: `test_bug_condition_test_suite_failures.py`

**Total Tests**: 10  
**Failed (Expected)**: 9  
**Passed**: 1 (summary test)

---

## Bug 1: Profile GET Method Missing

### Root Cause Confirmed
`GenericProfileView` in `triagesync_backend/apps/authentication/views.py` only implements `patch()` method, missing `get()` method.

### Counterexamples Found

1. **Test**: `test_authenticated_patient_get_profile_returns_200`
   - **Input**: GET `/api/v1/profile/` with valid patient JWT token
   - **Expected**: 200 OK with profile data
   - **Actual**: 404 Not Found
   - **Confirms**: GET method not implemented

2. **Test**: `test_authenticated_staff_get_profile_returns_200`
   - **Input**: GET `/api/v1/profile/` with valid staff JWT token
   - **Expected**: 200 OK with profile data
   - **Actual**: 404 Not Found
   - **Confirms**: GET method not implemented for any role

3. **Test**: `test_unauthenticated_get_profile_returns_401`
   - **Input**: GET `/api/v1/profile/` without authentication
   - **Expected**: 401 Unauthorized
   - **Actual**: 404 Not Found
   - **Confirms**: Missing method prevents proper authentication error handling

### Validation
✅ Bug exists - GenericProfileView lacks get() method implementation

---

## Bug 2: Dashboard Serializer Field Error

### Root Cause Confirmed
`DashboardPatientSerializer` in `triagesync_backend/apps/dashboard/serializers.py` references field `verified_by` but the actual `PatientSubmission` model field is named `verified_by_user`.

### Counterexamples Found

1. **Test**: `test_dashboard_serializer_no_improperly_configured_exception`
   - **Input**: GET `/api/v1/dashboard/staff/patients/` with staff token
   - **Expected**: 200 OK with serialized data
   - **Actual**: 500 Internal Server Error with `ImproperlyConfigured` exception
   - **Error Message**: `Field name 'verified_by' is not valid for model 'PatientSubmission'`
   - **Confirms**: Serializer references non-existent field

2. **Test**: `test_dashboard_pagination_serializes_successfully`
   - **Input**: GET `/api/v1/dashboard/staff/patients/` (pagination endpoint)
   - **Expected**: 200 OK with paginated data
   - **Actual**: 500 Internal Server Error with `ImproperlyConfigured` exception
   - **Confirms**: Field error affects pagination

3. **Test**: `test_dashboard_queue_filtering_serializes_successfully`
   - **Input**: GET `/api/v1/dashboard/staff/patients/?status=waiting` (filtering)
   - **Expected**: 200 OK with filtered data
   - **Actual**: 500 Internal Server Error with `ImproperlyConfigured` exception
   - **Confirms**: Field error affects all serialization operations

### Stack Trace Analysis
```
django.core.exceptions.ImproperlyConfigured: Field name `verified_by` is not valid 
for model `PatientSubmission` in `triagesync_backend.apps.dashboard.serializers.DashboardPatientSerializer`.
```

The error occurs during serializer field building in `rest_framework.serializers.py:1396` when Django REST Framework tries to map the field name to the model.

### Validation
✅ Bug exists - DashboardPatientSerializer uses wrong field name `verified_by` instead of `verified_by_user`

---

## Bug 3: Authentication Error Code Inconsistency

### Root Cause Confirmed
`LoginView` in `triagesync_backend/apps/authentication/views.py` line ~50 uses error code `INVALID_CREDENTIALS` instead of the standardized `AUTHENTICATION_FAILED`.

### Counterexamples Found

1. **Test**: `test_invalid_credentials_returns_authentication_failed_code`
   - **Input**: POST `/api/v1/auth/login/` with non-existent username and wrong password
   - **Expected**: Error code `AUTHENTICATION_FAILED`
   - **Actual**: Error code `INVALID_CREDENTIALS`
   - **Confirms**: Wrong error code used

2. **Test**: `test_wrong_password_returns_authentication_failed_code`
   - **Input**: POST `/api/v1/auth/login/` with valid username but wrong password
   - **Expected**: Error code `AUTHENTICATION_FAILED`
   - **Actual**: Error code `INVALID_CREDENTIALS`
   - **Confirms**: Inconsistent error code across all authentication failures

3. **Test**: `test_error_response_format_includes_code_and_message`
   - **Input**: POST `/api/v1/auth/login/` with invalid credentials
   - **Expected**: Error code `AUTHENTICATION_FAILED` with proper format
   - **Actual**: Error code `INVALID_CREDENTIALS` (format is correct, code is wrong)
   - **Confirms**: Error response format is correct, but code value is inconsistent

### Response Format
```json
{
  "code": "INVALID_CREDENTIALS",  // Should be "AUTHENTICATION_FAILED"
  "message": "Invalid username or password"
}
```

### Validation
✅ Bug exists - LoginView uses non-standard error code `INVALID_CREDENTIALS` instead of `AUTHENTICATION_FAILED`

---

## Conclusion

All three bugs have been confirmed through exploration tests:

1. ✅ **Profile GET Missing**: GenericProfileView lacks get() method → Returns 404 instead of profile data
2. ✅ **Dashboard Serializer Field Error**: DashboardPatientSerializer references `verified_by` instead of `verified_by_user` → Raises ImproperlyConfigured exception
3. ✅ **Auth Error Code Inconsistency**: LoginView uses `INVALID_CREDENTIALS` instead of `AUTHENTICATION_FAILED` → Returns non-standard error code

### Next Steps

These exploration tests encode the expected behavior. When the bugs are fixed in Phase 3 (Implementation), these same tests will PASS, confirming the fixes work correctly.

**DO NOT attempt to fix the tests or the code yet** - this is the exploration phase. The failures are expected and correct.

---

## Test File Location

`Django-Backend/test_bug_condition_test_suite_failures.py`

## Requirements Validated

- **Requirement 2.1**: Profile GET returns 200 OK with profile data
- **Requirement 2.3**: Profile GET without auth returns 401 Unauthorized
- **Requirement 2.5**: Profile GET with missing token returns 401
- **Requirement 2.6**: Dashboard serializer excludes non-existent field
- **Requirement 2.7**: Dashboard serialization succeeds without exceptions
- **Requirement 2.9**: Authentication failures return AUTHENTICATION_FAILED code
- **Requirement 2.10**: Error responses include code, message, and details fields
