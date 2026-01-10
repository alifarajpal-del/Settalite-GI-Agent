#!/usr/bin/env pwsh
# Quick Fix for 2000+ Problems in VS Code

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Quick Fix for 2000+ VS Code Problems" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "PROBLEM: SonarLint Extension showing 2000+ unnecessary warnings" -ForegroundColor Yellow
Write-Host ""

Write-Host "QUICK SOLUTIONS (choose one):" -ForegroundColor Green
Write-Host ""

Write-Host "Option 1: Disable SonarLint in VS Code:" -ForegroundColor White
Write-Host "   - Press Ctrl+Shift+X" -ForegroundColor Gray
Write-Host "   - Search for 'SonarLint'" -ForegroundColor Gray
Write-Host "   - Click 'Disable (Workspace)'" -ForegroundColor Gray
Write-Host ""

Write-Host "Option 2: Show Errors Only in Problems Panel:" -ForegroundColor White
Write-Host "   - Press Ctrl+Shift+M to open Problems" -ForegroundColor Gray
Write-Host "   - Click filter icon" -ForegroundColor Gray
Write-Host "   - Select 'Show Errors Only'" -ForegroundColor Gray
Write-Host ""

Write-Host "Option 3: Uninstall SonarLint Completely:" -ForegroundColor White
Write-Host "   - Ctrl+Shift+X -> SonarLint -> Uninstall" -ForegroundColor Gray
Write-Host ""

Write-Host "================================" -ForegroundColor Cyan
Write-Host "After applying, reload VS Code:" -ForegroundColor Cyan
Write-Host "   Ctrl+Shift+P -> 'Reload Window'" -ForegroundColor Gray
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Ask user what they want to do
Write-Host "Open full disable instructions? (y/n): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq 'y' -or $response -eq 'Y') {
    Start-Process "docs/DISABLE_SONARLINT.md"
    Write-Host "Instructions opened!" -ForegroundColor Green
} else {
    Write-Host "Remember: Ctrl+Shift+X -> SonarLint -> Disable" -ForegroundColor Green
}

Write-Host ""
Write-Host "Expected Result:" -ForegroundColor Cyan
Write-Host "   Before: 2000+ problems" -ForegroundColor Red
Write-Host "   After: ~50 real errors only" -ForegroundColor Green
