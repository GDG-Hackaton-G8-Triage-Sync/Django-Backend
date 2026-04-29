# Quick test summary script
$ErrorActionPreference = "Continue"

Write-Host "`n=== Running Django Test Suite ===" -ForegroundColor Cyan

# Run tests with summary only
$output = python -m pytest --tb=no -q --maxfail=1000 2>&1 | Out-String

# Extract summary line
$summary = $output -split "`n" | Where-Object { $_ -match "passed|failed|error" } | Select-Object -Last 1

Write-Host "`nTest Summary:" -ForegroundColor Yellow
Write-Host $summary -ForegroundColor White

# Count failures and errors
if ($output -match "(\d+) failed") {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $output -split "`n" | Where-Object { $_ -match "FAILED" } | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Red
    }
}

if ($output -match "(\d+) error") {
    Write-Host "`nErrors:" -ForegroundColor Red
    $output -split "`n" | Where-Object { $_ -match "ERROR" } | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Red
    }
}
