#Requires -Version 5.1
# ============================================
# Fix npm install issues
# ============================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  FIX NPM INSTALL - FRONTEND" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Clean old installation
if (Test-Path "node_modules") {
    Write-Host "[1/4] Removing old node_modules..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
    Write-Host "  [OK] Removed" -ForegroundColor Green
} else {
    Write-Host "[1/4] No node_modules to remove" -ForegroundColor Gray
}

if (Test-Path "package-lock.json") {
    Write-Host "[2/4] Removing old package-lock.json..." -ForegroundColor Yellow
    Remove-Item -Force "package-lock.json" -ErrorAction SilentlyContinue
    Write-Host "  [OK] Removed" -ForegroundColor Green
} else {
    Write-Host "[2/4] No package-lock.json to remove" -ForegroundColor Gray
}

# Ensure iconify-icons directory exists
Write-Host "[3/4] Creating iconify-icons directory..." -ForegroundColor Yellow
$iconifyPath = "src/assets/iconify-icons"
if (-not (Test-Path $iconifyPath)) {
    New-Item -ItemType Directory -Force -Path $iconifyPath | Out-Null
}
Write-Host "  [OK] Directory ready" -ForegroundColor Green

# Fresh install
Write-Host "[4/4] Installing npm packages..." -ForegroundColor Yellow
Write-Host "  This may take 2-3 minutes..." -ForegroundColor Cyan

try {
    npm install --legacy-peer-deps 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] npm packages installed successfully" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] npm install failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Try manually:" -ForegroundColor Yellow
        Write-Host "  cd mvp\frontend" -ForegroundColor White
        Write-Host "  npm install --legacy-peer-deps" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  NPM INSTALL FIXED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run: .\start-env.bat" -ForegroundColor Cyan
Write-Host ""

