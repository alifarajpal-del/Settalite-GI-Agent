#!/usr/bin/env pwsh
# Quick Fix for 2000+ Problems in VS Code

Write-Host "================================" -ForegroundColor Cyan
Write-Host "حل سريع لمشكلة 2000+ خطأ في VS Code" -ForegroundColor Cyan
Write-Host "Quick Fix for 2000+ VS Code Problems" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "المشكلة: SonarLint Extension يعرض 2000+ تحذير غير ضروري" -ForegroundColor Yellow
Write-Host "Problem: SonarLint Extension showing 2000+ unnecessary warnings" -ForegroundColor Yellow
Write-Host ""

Write-Host "الحل السريع (اختر واحدة):" -ForegroundColor Green
Write-Host "Quick Solution (choose one):" -ForegroundColor Green
Write-Host ""

Write-Host "1️⃣  تعطيل SonarLint من VS Code:" -ForegroundColor White
Write-Host "   - اضغط Ctrl+Shift+X" -ForegroundColor Gray
Write-Host "   - ابحث عن 'SonarLint'" -ForegroundColor Gray
Write-Host "   - اضغط 'Disable (Workspace)'" -ForegroundColor Gray
Write-Host ""

Write-Host "2️⃣  إظهار الأخطاء فقط في Problems Panel:" -ForegroundColor White
Write-Host "   - اضغط Ctrl+Shift+M لفتح Problems" -ForegroundColor Gray
Write-Host "   - اضغط على أيقونة الفلتر (⏷)" -ForegroundColor Gray  
Write-Host "   - اختر 'Show Errors Only'" -ForegroundColor Gray
Write-Host ""

Write-Host "3️⃣  إزالة SonarLint بالكامل:" -ForegroundColor White
Write-Host "   - Ctrl+Shift+X → SonarLint → Uninstall" -ForegroundColor Gray
Write-Host ""

Write-Host "================================" -ForegroundColor Cyan
Write-Host "بعد التطبيق، أعد تحميل VS Code:" -ForegroundColor Cyan
Write-Host "After applying, reload VS Code:" -ForegroundColor Cyan
Write-Host "   Ctrl+Shift+P → 'Reload Window'" -ForegroundColor Gray
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Ask user what they want to do
Write-Host "هل تريد فتح دليل التعطيل الكامل؟" -ForegroundColor Yellow
Write-Host "Open full disable instructions?" -ForegroundColor Yellow
$response = Read-Host "(y/n)"

if ($response -eq 'y' -or $response -eq 'Y') {
    Start-Process "docs/DISABLE_SONARLINT.md"
    Write-Host "✅ تم فتح الدليل!" -ForegroundColor Green
} else {
    Write-Host "✅ تذكر: Ctrl+Shift+X → SonarLint → Disable" -ForegroundColor Green
}

Write-Host ""
Write-Host "📊 النتيجة المتوقعة:" -ForegroundColor Cyan
Write-Host "   قبل: 2000+ مشكلة ❌" -ForegroundColor Red
Write-Host "   بعد: ~50 خطأ حقيقي فقط ✅" -ForegroundColor Green
