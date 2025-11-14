#Requires -Version 5.1
# ============================================
# SaaS-IA Environment Stop Script
# Version: 1.0.0
# ============================================

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Paths
$SAAS_IA_ROOT = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$MVP_ROOT = Join-Path $SAAS_IA_ROOT "mvp"
$BACKEND = Join-Path $MVP_ROOT "backend"
$FRONTEND = Join-Path $MVP_ROOT "frontend"

# Colors
function Log($msg, $col="White") { 
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor $col 
}

function Step($msg) { 
    Log "`n========== $msg ==========" "Magenta" 
}

# ============================================
# MAIN EXECUTION
# ============================================

Clear-Host

Log ""
Log "===========================================================" "Cyan"
Log "         SAAS-IA ENVIRONMENT - STOP                       " "Cyan"
Log "===========================================================" "Cyan"
Log ""

Step "STOPPING PROCESSES        "

# Stop Frontend (Node.js on port 3002)
$frontendProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*SaaS-IA*" -or 
    (Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 3002 })
}

if ($frontendProcesses) {
    $frontendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Log "  [OK] Stopped Frontend (Node.js port 3002)" "Cyan"
} else {
    Log "  [INFO] Frontend not running" "Gray"
}

# Stop Backend (Python on port 8004 - external mapping)
$backendProcesses = Get-Process python,uvicorn -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*SaaS-IA*" -or 
    (Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 8004 })
}

if ($backendProcesses) {
    $backendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Log "  [OK] Stopped Backend (Python port 8004)" "Cyan"
} else {
    Log "  [INFO] Backend not running" "Gray"
}

# Stop Docker containers
Push-Location $BACKEND
$dockerOutput = docker-compose down --remove-orphans 2>&1
Pop-Location

if ($LASTEXITCODE -eq 0) {
    Log "  [OK] Stopped Docker containers (PostgreSQL:5435, Redis:6382)" "Cyan"
} else {
    Log "  [WARN] Docker containers already stopped or not found" "Yellow"
}

Log ""
Log "===========================================================" "Green"
Log "         [SUCCESS] SAAS-IA ENVIRONMENT STOPPED            " "Green"
Log "===========================================================" "Green"
Log ""
Log "All services have been stopped successfully." "White"
Log ""
Log "To restart: run start-env.bat or restart-env.bat" "Cyan"
Log ""
