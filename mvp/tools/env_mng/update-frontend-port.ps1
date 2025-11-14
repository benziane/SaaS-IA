#Requires -Version 5.1
# ============================================
# Update Frontend Port: 3002 → 5174
# ============================================

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n🔧 MISE À JOUR PORT FRONTEND: 3002 → 5174`n" -ForegroundColor Cyan

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
        
        # Remplacer 3002 par 5174
        $content = $content -replace '3002', '5174'
        
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

Write-Host "`n✅ TERMINÉ: $replacements fichier(s) mis à jour`n" -ForegroundColor Green
Write-Host "🚀 Nouveau port frontend: http://localhost:5174`n" -ForegroundColor Cyan

