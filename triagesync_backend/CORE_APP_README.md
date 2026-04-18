# Core App - Shared Utilities Module

**Version:** 1.0.0
**Status:** Production Ready
**Purpose:** Centralized utilities, constants, and standards for TriageSync Backend

---

## Overview

The Core App (`apps/core/`) provides shared functionality used across all modules in the TriageSync system. It ensures consistency, reduces code duplication, and maintains standardized patterns throughout the application.

---

## Architecture

```
apps/core/
├── __init__.py          # Module initialization
├── constants.py         # System-wide constants and enums
├── utils.py             # Validation and utility functions
├── response.py          # Standardized API response formats
├── exceptions.py        # Custom exception classes
└── middleware.py        # Global exception handling
```

---

## Core Components

### 1. Constants Module (`constants.py`)

Defines all system-wide constants to prevent magic strings and ensure type safety.

#### User Roles

```python
UserRole.PATIENT = 'patient'
UserRole.STAFF = 'staff'
UserRole.ADMIN = 'admin'
```

#### Patient Status

```python
PatientStatus.WAITING = 'waiting'
PatientStatus.IN_PROGRESS = 'in_progress'
PatientStatus.COMPLETED = 'completed'
```

#### Triage Priority (1-5 Scale)

```python
TriagePriority.CRITICAL = 1    # Life-threatening (90-100 urgency)
TriagePriority.HIGH = 2        # Urgent (70-89 urgency)
TriagePriority.MODERATE = 3    # Moderate (50-69 urgency)
TriagePriority.LOW = 4         # Low (30-49 urgency)
TriagePriority.MINIMAL = 5     # Minimal (0-29 urgency)
```

#### WebSocket Event Types

```python
WSEventType.PATIENT_CREATED = 'patient_created'
WSEventType.PRIORITY_UPDATE = 'priority_update'
WSEventType.STATUS_UPDATE = 'status_update'
WSEventType.CRITICAL_ALERT = 'critical_alert'
```

---

### 2. Utilities Module (`utils.py`)

Provides validation, sanitization, and helper functions.

#### Validation Functions

- `validate_priority(priority)` - Validates priority is 1-5
- `validate_urgency_score(score)` - Validates score is 0-100

#### Sanitization Functions

- `sanitize_input(text, max_length)` - Cleans and truncates user input

#### DateTime Functions

- `get_current_timestamp()` - Returns current UTC timestamp
- `format_datetime(dt)` - Formats datetime to ISO 8601

---

### 3. Response Module (`response.py`)

Standardizes all API responses for consistency.

#### Success Responses

- `success_response(data, message, status_code)` - 200 OK
- `created_response(data, message)` - 201 Created

#### Error Responses

- `error_response(error, details, status_code)` - 400 Bad Request
- `validation_error_response(error, details)` - 400 Validation Error
- `unauthorized_response(error)` - 401 Unauthorized
- `forbidden_response(error)` - 403 Forbidden
- `not_found_response(error)` - 404 Not Found
- `server_error_response(error)` - 500 Internal Server Error

---

### 4. Exceptions Module (`exceptions.py`)

Custom exception classes for specific error scenarios.

#### Exception Classes

- `TriageException` - Base exception (500)
- `AIServiceException` - AI service failures (503)
- `ValidationException` - Validation errors (400)
- `PermissionDeniedException` - Permission errors (403)

#### Exception Handler

- `custom_exception_handler(exc, context)` - Formats all exceptions consistently

---

### 5. Middleware Module (`middleware.py`)

Global exception handling middleware.

#### ExceptionHandlerMiddleware

- Catches all unhandled exceptions
- Logs errors for debugging
- Returns standardized JSON responses
- Hides sensitive details from non-staff users

---

## Usage Examples

### Using Constants

```python
from apps.core.constants import UserRole, TriagePriority

# Check user role
if user.role == UserRole.ADMIN:
    # Admin logic
    pass

# Check priority
if submission.priority == TriagePriority.CRITICAL:
    send_alert()
```

### Using Validation

```python
from apps.core.utils import validate_priority, sanitize_input

# Validate input
priority = request.data.get('priority')
if not validate_priority(priority):
    return error_response('Invalid priority (1-5)')

# Sanitize input
description = sanitize_input(
    request.data.get('description'),
    max_length=500
)
```

### Using Responses

```python
from apps.core.response import success_response, error_response

# Success
return success_response({'id': 1, 'status': 'processed'})

# Error
return error_response('Invalid input', details={'field': 'Required'})
```

### Using Exceptions

```python
from apps.core.exceptions import AIServiceException

# Raise exception
if ai_service_down:
    raise AIServiceException('AI service unavailable')

# Catch exception
try:
    result = process_triage()
except AIServiceException as e:
    logger.error(f'AI failed: {str(e)}')
    return error_response('Service temporarily unavailable')
```

---

## Integration Points

### Used By

- **Authentication App** - User roles, response formats
- **Patients App** - Status constants, validation
- **Triage App** - Priority constants, exceptions
- **Dashboard App** - All utilities and constants
- **Realtime App** - WebSocket event types

### Dependencies

- Django 5.1.5
- Django REST Framework 3.15.2
- Python 3.11+

---

## Best Practices

### 1. Always Use Constants

```python
# ❌ Bad - Magic strings
if user.role == 'admin':
    pass

# ✅ Good - Type-safe constants
if user.role == UserRole.ADMIN:
    pass
```

### 2. Validate All Inputs

```python
# ✅ Always validate before processing
if not validate_priority(priority):
    return error_response('Invalid priority')
```

### 3. Sanitize User Data

```python
# ✅ Clean user input
description = sanitize_input(request.data.get('description'), max_length=500)
```

### 4. Use Standard Responses

```python
# ✅ Consistent response format
return success_response({'id': 1})
return error_response('Not found')
```

### 5. Raise Specific Exceptions

```python
# ✅ Use appropriate exception types
raise ValidationException('Invalid data')
raise AIServiceException('Service unavailable')
```

---

## Testing

Run comprehensive tests:

```bash
python test_core_app.py
```

**Test Coverage:**

- 24 constant definitions
- 16 validation test cases
- 6 sanitization test cases
- 4 datetime test cases
- 12 response function tests
- 8 exception tests
- 8 edge case tests

**Total: 78 tests covering 100% of core functionality**

---

## Error Handling Flow

```
Request → View → Validation (utils.py)
                      ↓
                 Processing
                      ↓
              Exception? → Custom Exception (exceptions.py)
                      ↓
              Exception Handler (exceptions.py)
                      ↓
              Middleware (middleware.py)
                      ↓
              Standard Response (response.py)
                      ↓
                   Client
```

---

## Response Format Standards

### Success Response

```json
{
  "id": 1,
  "status": "processed",
  "message": "Operation successful"
}
```

### Error Response

```json
{
  "error": "Invalid input",
  "details": {
    "field": "This field is required"
  }
}
```

---

## Configuration

No configuration required. Core app is automatically loaded when Django starts.

---

## Maintenance

### Adding New Constants

1. Add to appropriate class in `constants.py`
2. Update `CHOICES` if applicable
3. Document in this README
4. Add tests in `test_core_app.py`

### Adding New Utilities

1. Add function to `utils.py`
2. Add docstring with examples
3. Add validation/error handling
4. Add comprehensive tests

### Adding New Exceptions

1. Inherit from `TriageException`
2. Set appropriate `status_code`
3. Add to `exceptions.py`
4. Document usage

---

## Security Considerations

1. **Input Sanitization** - Always use `sanitize_input()` for user data
2. **Validation** - Validate all inputs before processing
3. **Error Messages** - Hide sensitive details from non-staff users
4. **Logging** - All exceptions are logged for audit trail
5. **Type Safety** - Use constants to prevent injection attacks

---

## Performance

- **Constants** - Zero overhead (compile-time)
- **Validation** - O(1) complexity
- **Sanitization** - O(n) where n = string length
- **Response Functions** - Minimal overhead
- **Exception Handling** - Only on error paths

---

## Troubleshooting

### Import Errors

```python
# ❌ Wrong
from core.constants import UserRole

# ✅ Correct
from apps.core.constants import UserRole
```

### Validation Not Working

```python
# Ensure correct type
priority = int(request.data.get('priority'))
if not validate_priority(priority):
    return error_response('Invalid priority')
```

### Response Format Issues

```python
# Use appropriate response function
return success_response(data)  # Not Response(data)
```

---

## API Reference

See [CORE_APP_API.md](CORE_APP_API.md) for complete API documentation.

---

## Support

For issues or questions:

1. Check test results: `python test_core_app.py`
2. Review API documentation: `CORE_APP_API.md`
3. Check Django logs: `logs/error.log`
