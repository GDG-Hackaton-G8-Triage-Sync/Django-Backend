# Bug Condition Exploration Test Results

## Task 1: Write Bug Condition Exploration Test

**Status**: ✅ COMPLETE

**Test File**: `Django-Backend/triagesync_backend/apps/triage/tests/test_ai_timeout_bug_condition.py`

## Test Overview

The bug condition exploration test has been written and updated with proper mocking to test the AI timeout bug. The test file contains 5 test cases:

### Test Cases

1. **test_10_second_response_should_succeed** - Tests API call with 10-second response time
2. **test_15_second_response_should_succeed** - Tests API call with 15-second response time  
3. **test_20_second_response_should_succeed** - Tests API call with 20-second response time
4. **test_25_second_response_should_succeed** - Tests API call with 25-second response time
5. **test_35_second_response_should_timeout** - Tests API call with 35-second response time (preservation test)

## Expected Behavior

### On Unfixed Code (8-second timeout):
- Tests 1-4 (10s, 15s, 20s, 25s): **EXPECTED TO FAIL** with TimeoutError
  - This confirms the bug exists - API calls timing out between 8-30 seconds
- Test 5 (35s): **EXPECTED TO FAIL** with TimeoutError (exceeds any reasonable timeout)

### On Fixed Code (30-second timeout):
- Tests 1-4 (10s, 15s, 20s, 25s): **SHOULD PASS** - API calls complete successfully
- Test 5 (35s): **SHOULD FAIL** with TimeoutError (exceeds the new 30s timeout)

## Test Implementation Details

The tests use:
- `@override_settings(GEMINI_TIMEOUT_SECONDS=8)` to enforce the 8-second timeout on unfixed code
- Mocking of `genai.GenerativeModel`, `genai.configure`, and `genai.list_models` to avoid real API calls
- `time.sleep()` to simulate actual API response delays
- Assertions that check for successful triage data (not timeout errors)

## Counterexamples to be Documented

When run on unfixed code, the tests will surface counterexamples such as:

- **10s response**: API call with 10s response time raises TimeoutError at 8s instead of waiting and returning valid triage data
- **15s response**: API call with 15s response time raises TimeoutError at 8s instead of waiting and returning valid triage data
- **20s response**: API call with 20s response time raises TimeoutError at 8s instead of waiting and returning valid triage data
- **25s response**: API call with 25s response time raises TimeoutError at 8s instead of waiting and returning valid triage data

## Requirements Validated

**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2**

- 1.1: WHEN the Gemini API takes longer than 8 seconds to respond THEN the system raises a TimeoutError
- 1.2: WHEN a TimeoutError occurs THEN the system falls back to the next model or returns an error
- 1.3: WHEN multiple models timeout within 8 seconds THEN users receive "AI unavailable" errors
- 2.1: WHEN the Gemini API takes 8-30 seconds THEN the system SHALL wait for the response (after fix)
- 2.2: WHEN the Gemini API responds within increased timeout THEN the system SHALL process successfully (after fix)

## Next Steps

1. Run the test suite on unfixed code to confirm failures and document counterexamples
2. Apply the fix (increase timeout from 8s to 30s in settings.py and ai_service.py)
3. Re-run the test suite to verify tests 1-4 now pass while test 5 still fails appropriately
4. Document the successful fix validation

## Notes

- The tests are designed to actually sleep for the specified durations to accurately simulate API response times
- Each test takes the full duration to complete (10s, 15s, 20s, 25s, 35s respectively)
- Total test suite runtime on unfixed code: ~8s × 5 tests = ~40s (all timeout at 8s)
- Total test suite runtime on fixed code: 10s + 15s + 20s + 25s + 30s = ~100s
