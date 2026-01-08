# Heritage Sentinel Pro - One-Command Verification
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "`nHeritage Sentinel Pro - Full Verification`n" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

$allPassed = $true

Write-Host "`n[1/2] Running smoke test..." -ForegroundColor Cyan
& ".\scripts\smoke_test.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Smoke test" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "PASSED: Smoke test" -ForegroundColor Green
}

Write-Host "`n[2/2] Running integration test..." -ForegroundColor Cyan
python test_integration.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Integration test" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "PASSED: Integration test" -ForegroundColor Green
}

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "`nVERIFIED: Demo mode ready" -ForegroundColor Green
    Write-Host "`nYou can now run:" -ForegroundColor Cyan
    Write-Host "  streamlit run run.py" -ForegroundColor White
    exit 0
} else {
    Write-Host "`nVERIFICATION FAILED" -ForegroundColor Red
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Check errors above" -ForegroundColor Gray
    Write-Host "  2. Install missing dependencies:" -ForegroundColor Gray
    Write-Host "     pip install -r requirements_core.txt" -ForegroundColor White
    Write-Host "  3. Re-run verification script" -ForegroundColor Gray
    exit 1
}
