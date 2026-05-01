# Run all tests and collect results
$ErrorActionPreference = "Continue"

Write-Host "Running Django Backend Test Suite" -ForegroundColor Cyan
Write-Host "==================================`n" -ForegroundColor Cyan

# Run tests and capture output
python -m pytest --tb=short -v --maxfail=1000 2>&1 | Tee-Object -FilePath test_output.log

# Show summary
Write-Host "`n`nTest Summary:" -ForegroundColor Cyan
Write-Host "=============`n" -ForegroundColor Cyan
Get-Content test_output.log | Select-String "passed|failed|error" | Select-Object -Last 5
