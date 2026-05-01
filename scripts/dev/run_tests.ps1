# Run Tests with D: Drive Configuration
# This script configures the environment to use D: drive for all temporary files

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "API CONTRACT COMPLETION - TEST RUNNER" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Set environment to use D: drive
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:TMPDIR = "D:\Temp"
$env:PYTEST_CACHE_DIR = "D:\pytest_cache"

Write-Host "Environment Configuration:" -ForegroundColor Green
Write-Host "  TEMP: $env:TEMP" -ForegroundColor White
Write-Host "  TMP: $env:TMP" -ForegroundColor White
Write-Host "  PYTEST_CACHE: $env:PYTEST_CACHE_DIR" -ForegroundColor White

Write-Host "`nOptimizations Applied:" -ForegroundColor Green
Write-Host "   NeonDB connection pooling (10 min)" -ForegroundColor White
Write-Host "   Connection health checks" -ForegroundColor White
Write-Host "   Connection timeout: 10s" -ForegroundColor White
Write-Host "   Statement timeout: 30s" -ForegroundColor White
Write-Host "   Test DB reuse" -ForegroundColor White
Write-Host "   No migrations during tests" -ForegroundColor White
Write-Host "   D: drive for temp files" -ForegroundColor White

Write-Host "`nRunning tests..." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Run pytest
python -m pytest test_integration_api_contract_completion.py -v --tb=short

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test execution complete" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan