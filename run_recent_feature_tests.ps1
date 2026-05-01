# PowerShell script to run all recent feature tests
# Tests cover: Blood Type Enhancement, Prompt Tuning, Required Fields Update

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Recent Features Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to Django-Backend directory
Set-Location -Path "Django-Backend"

Write-Host "Test Coverage:" -ForegroundColor Yellow
Write-Host "  1. Blood Type Normalization" -ForegroundColor White
Write-Host "  2. Demographic Normalization (Age, Gender)" -ForegroundColor White
Write-Host "  3. AI Service Integration" -ForegroundColor White
Write-Host "  4. Prompt Engine (ESI Framework, Red Flags)" -ForegroundColor White
Write-Host "  5. Registration Serializer Validation" -ForegroundColor White
Write-Host "  6. Required Fields Enforcement" -ForegroundColor White
Write-Host "  7. Blood Transfusion Guidance" -ForegroundColor White
Write-Host "  8. API Integration Tests" -ForegroundColor White
Write-Host ""

# Run triage tests
Write-Host "========================================" -ForegroundColor Green
Write-Host "Running Triage Feature Tests..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
python manage.py test triagesync_backend.apps.triage.tests.test_recent_features --verbosity=2

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Triage tests failed!" -ForegroundColor Red
    Set-Location -Path ".."
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Running Authentication Tests..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
python manage.py test triagesync_backend.apps.authentication.tests --verbosity=2

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Authentication tests failed!" -ForegroundColor Red
    Set-Location -Path ".."
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Running Blood Type Checkpoint Tests..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
python manage.py test triagesync_backend.apps.triage.tests.test_blood_type_checkpoint --verbosity=2

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Blood type checkpoint tests failed!" -ForegroundColor Red
    Set-Location -Path ".."
    exit 1
}

# Return to original directory
Set-Location -Path ".."

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All Tests Passed Successfully! ✓" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Blood Type Normalization Tests" -ForegroundColor Green
Write-Host "  ✓ Demographic Normalization Tests" -ForegroundColor Green
Write-Host "  ✓ AI Service Integration Tests" -ForegroundColor Green
Write-Host "  ✓ Prompt Engine Tests" -ForegroundColor Green
Write-Host "  ✓ Registration Validation Tests" -ForegroundColor Green
Write-Host "  ✓ Required Fields Tests" -ForegroundColor Green
Write-Host "  ✓ Blood Transfusion Guidance Tests" -ForegroundColor Green
Write-Host "  ✓ API Integration Tests" -ForegroundColor Green
Write-Host ""
