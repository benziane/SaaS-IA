#Requires -Version 5.1
<#
.SYNOPSIS
    Test Backend-Only : Transcription Complète
    
.DESCRIPTION
    Lance un test complet de transcription YouTube avec amélioration AI
    en arrière-plan, sans interface utilisateur.
    
.EXAMPLE
    .\run_transcription_test.ps1
#>

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TEST TRANSCRIPTION COMPLETE" -ForegroundColor Green
Write-Host "  Backend-Only (No UI)" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "[CHECK] Verifying Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Docker is running" -ForegroundColor Green

# Check if backend container is running
Write-Host "[CHECK] Verifying backend container..." -ForegroundColor Yellow
$backendRunning = docker ps --filter "name=saas-ia-backend" --format "{{.Names}}"
if (-not $backendRunning) {
    Write-Host "[ERROR] Backend container is not running!" -ForegroundColor Red
    Write-Host "Please start the backend: cd backend && docker-compose up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Backend container is running" -ForegroundColor Green

Write-Host "`n[INFO] Running transcription test inside Docker..." -ForegroundColor Cyan
Write-Host "[INFO] This will take 30-60 seconds..." -ForegroundColor Yellow
Write-Host "`n" + ("-" * 80) + "`n" -ForegroundColor Gray

# Run test inside Docker container (no -it for non-interactive)
docker exec saas-ia-backend python test_transcription_complete.py

$exitCode = $LASTEXITCODE

Write-Host "`n" + ("-" * 80) + "`n" -ForegroundColor Gray

if ($exitCode -eq 0) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  TEST PASSED ✅" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan
    Write-Host "[SUCCESS] Transcription test completed successfully!" -ForegroundColor Green
    Write-Host "`n[RESULTS] Check the output above for:" -ForegroundColor Yellow
    Write-Host "  - Raw text (AssemblyAI)" -ForegroundColor White
    Write-Host "  - Improved text (AI)" -ForegroundColor White
    Write-Host "  - Comparison stats" -ForegroundColor White
    Write-Host "  - AI provider used (FREE 🆓)" -ForegroundColor White
} else {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  TEST FAILED ❌" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Cyan
    Write-Host "[ERROR] Transcription test failed!" -ForegroundColor Red
    Write-Host "[DEBUG] Check the error messages above" -ForegroundColor Yellow
}

Write-Host "`n[TIP] To see backend logs:" -ForegroundColor Yellow
Write-Host "  docker logs saas-ia-backend -f`n" -ForegroundColor White

exit $exitCode

