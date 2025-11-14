#Requires -Version 5.1
# ============================================
# Test Scripts Syntax
# ============================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  TEST DES SCRIPTS - VALIDATION SYNTAXE" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$scripts = @("start-env.ps1", "stop-env.ps1", "restart-env.ps1", "check-status.ps1")
$errors = @()

foreach ($script in $scripts) {
    if (Test-Path $script) {
        try {
            $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $script -Raw), [ref]$null)
            Write-Host "  [OK] $script - Syntaxe valide" -ForegroundColor Green
        } catch {
            Write-Host "  [ERROR] $script - $($_.Exception.Message)" -ForegroundColor Red
            $errors += $script
        }
    } else {
        Write-Host "  [WARN] $script - Fichier non trouve" -ForegroundColor Yellow
    }
}

Write-Host ""
if ($errors.Count -eq 0) {
    Write-Host "[SUCCESS] Tous les scripts ont une syntaxe valide !" -ForegroundColor Green
} else {
    Write-Host "[ERROR] $($errors.Count) script(s) avec erreurs: $($errors -join ', ')" -ForegroundColor Red
}
Write-Host ""

