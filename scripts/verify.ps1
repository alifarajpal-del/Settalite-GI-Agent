# Heritage Sentinel Pro - One-Command Verification
# Runs all tests to verify repo is ready

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "`n🔍 Heritage Sentinel Pro - Full Verification`n" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

$allPassed = $true

# Step 1: Smoke test
Write-Host "`n1️⃣  Running smoke test..." -ForegroundColor Cyan
& ".\scripts\smoke_test.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Smoke test failed" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "✅ Smoke test passed" -ForegroundColor Green
}

# Step 2: Integration test
Write-Host "`n2️⃣  Running integration test..." -ForegroundColor Cyan
python test_integration.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Integration test failed" -ForegroundColor Red
    $allPassed = $false
} else {
    Write-Host "✅ Integration test passed" -ForegroundColor Green
}

# Final result
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "`n✅ VERIFIED: Demo mode ready" -ForegroundColor Green
    Write-Host "`nYou can now run:" -ForegroundColor Cyan
    Write-Host "  streamlit run run.py" -ForegroundColor White
    exit 0
} else {
    Write-Host "`n❌ VERIFICATION FAILED" -ForegroundColor Red
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Check errors above" -ForegroundColor Gray
    Write-Host "  2. Install missing dependencies:" -ForegroundColor Gray
    Write-Host "     pip install -r requirements_core.txt" -ForegroundColor White
    Write-Host "  3. Re-run: .\scripts\verify.ps1" -ForegroundColor Gray
    exit 1
}
