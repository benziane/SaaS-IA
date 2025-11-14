#Requires -Version 5.1
# ============================================
# Fix Port Conflict: 5174 → 3002
# Reason: 5174 is used by WeLAB
# ============================================

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n🔧 CORRECTION CONFLIT DE PORTS: 5174 → 3002`n" -ForegroundColor Red
Write-Host "Raison: Port 5174 déjà utilisé par WeLAB`n" -ForegroundColor Yellow

$files = @(
    "check-status.ps1",
    "restart-env.ps1",
    "start-env.ps1",
    "stop-env.ps1",
    "quick-commands.bat",
    "README.md",
    "INDEX.md",
    "TESTS_VALIDATION.md"
)

$replacements = 0

foreach ($file in $files) {
    $filePath = Join-Path $PSScriptRoot $file
    
    if (Test-Path $filePath) {
        Write-Host "📝 Mise à jour: $file" -ForegroundColor Yellow
        
        $content = Get-Content $filePath -Raw -Encoding UTF8
        $originalContent = $content
        
        # Remplacer 5174 par 3002
        $content = $content -replace '5174', '3002'
        
        if ($content -ne $originalContent) {
            Set-Content -Path $filePath -Value $content -Encoding UTF8 -NoNewline
            $replacements++
            Write-Host "   ✅ Mis à jour" -ForegroundColor Green
        } else {
            Write-Host "   ⏭️  Aucun changement nécessaire" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  Fichier non trouvé: $file" -ForegroundColor Red
    }
}

# Mettre à jour frontend
Write-Host "`n📝 Mise à jour: frontend/vite.config.ts" -ForegroundColor Yellow
$viteConfigPath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "frontend\vite.config.ts"

if (Test-Path $viteConfigPath) {
    $content = Get-Content $viteConfigPath -Raw -Encoding UTF8
    $originalContent = $content
    
    # Remplacer port: 5174 par port: 3002
    $content = $content -replace 'port:\s*5174', 'port: 3002'
    
    if ($content -ne $originalContent) {
        Set-Content -Path $viteConfigPath -Value $content -Encoding UTF8 -NoNewline
        $replacements++
        Write-Host "   ✅ Mis à jour" -ForegroundColor Green
    } else {
        Write-Host "   ⏭️  Aucun changement nécessaire" -ForegroundColor Gray
    }
} else {
    Write-Host "   ⚠️  Fichier non trouvé: vite.config.ts" -ForegroundColor Red
}

# Mettre à jour docs frontend
Write-Host "`n📝 Mise à jour: frontend/SNEAT_INTEGRATION_FINAL_REPORT.md" -ForegroundColor Yellow
$reportPath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "frontend\SNEAT_INTEGRATION_FINAL_REPORT.md"

if (Test-Path $reportPath) {
    $content = Get-Content $reportPath -Raw -Encoding UTF8
    $originalContent = $content
    
    $content = $content -replace '5174', '3002'
    
    if ($content -ne $originalContent) {
        Set-Content -Path $reportPath -Value $content -Encoding UTF8 -NoNewline
        $replacements++
        Write-Host "   ✅ Mis à jour" -ForegroundColor Green
    }
}

Write-Host "`n📝 Mise à jour: frontend/TESTS_VALIDATION_SNEAT.md" -ForegroundColor Yellow
$testsPath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "frontend\TESTS_VALIDATION_SNEAT.md"

if (Test-Path $testsPath) {
    $content = Get-Content $testsPath -Raw -Encoding UTF8
    $originalContent = $content
    
    $content = $content -replace '5174', '3002'
    
    if ($content -ne $originalContent) {
        Set-Content -Path $testsPath -Value $content -Encoding UTF8 -NoNewline
        $replacements++
        Write-Host "   ✅ Mis à jour" -ForegroundColor Green
    }
}

Write-Host "`n✅ TERMINÉ: $replacements fichier(s) mis à jour`n" -ForegroundColor Green
Write-Host "📊 RÉCAPITULATIF DES PORTS:`n" -ForegroundColor Cyan
Write-Host "  WeLAB     : Frontend 5174 | Backend 8001" -ForegroundColor Gray
Write-Host "  LabSaaS   : Frontend 5173 | Backend 8000" -ForegroundColor Gray
Write-Host "  SaaS-IA   : Frontend 3002 | Backend 8004" -ForegroundColor Green
Write-Host "`n🚀 Nouveau port frontend SaaS-IA: http://localhost:3002`n" -ForegroundColor Cyan

