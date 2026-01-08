# Heritage Sentinel Pro - Windows Smoke Test
# Tests critical paths and imports before running the app

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "`n🛰️  Heritage Sentinel Pro - Smoke Test`n" -ForegroundColor Cyan

# Check and activate venv if exists
if (Test-Path "heritage_env\Scripts\Activate.ps1") {
    Write-Host "✅ Virtual environment found, activating..." -ForegroundColor Green
    & ".\heritage_env\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  Virtual environment not found at heritage_env\" -ForegroundColor Yellow
    Write-Host "   Run: python -m venv heritage_env" -ForegroundColor Gray
}

$failures = 0
$warnings = 0

# Check critical files
Write-Host "`n📁 Checking critical files..." -ForegroundColor Cyan
$criticalFiles = @(
    "app\app.py",
    "run.py",
    "requirements.txt",
    "src\config\__init__.py",
    "src\services\mock_data_service.py"
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file MISSING" -ForegroundColor Red
        $failures++
    }
}

# Check Python imports
Write-Host "`n📦 Checking Python imports..." -ForegroundColor Cyan

$requiredImports = @("streamlit", "numpy", "pandas")
$recommendedImports = @("geopandas", "shapely", "pydeck", "folium")

foreach ($module in $requiredImports) {
    $result = python -c "import $module; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $module" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $module MISSING (required)" -ForegroundColor Red
        $failures++
    }
}

foreach ($module in $recommendedImports) {
    $result = python -c "import $module; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $module" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $module missing (recommended)" -ForegroundColor Yellow
        $warnings++
    }
}

# Run Python smoke test if available
if (Test-Path "scripts\smoke_test.py") {
    Write-Host "`n🐍 Running Python smoke test..." -ForegroundColor Cyan
    python scripts\smoke_test.py
    if ($LASTEXITCODE -ne 0) {
        $failures++
    }
} else {
    Write-Host "`n⚠️  scripts\smoke_test.py not found, skipping" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
if ($failures -eq 0) {
    Write-Host "✅ SMOKE TEST PASSED" -ForegroundColor Green
    if ($warnings -gt 0) {
        Write-Host "⚠️  $warnings warnings (non-critical)" -ForegroundColor Yellow
    }
    exit 0
} else {
    Write-Host "❌ SMOKE TEST FAILED: $failures critical failures" -ForegroundColor Red
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Install requirements: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "  2. Verify all files exist in src/ directory" -ForegroundColor Gray
    exit 1
}
