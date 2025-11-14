#Requires -Version 5.1
# ============================================
# SaaS-IA Environment Restart Script
# Version: 1.0.0
# ============================================

param(
    [switch]$KeepDB = $false,
    [switch]$SkipBrowser = $false,
    [ValidateSet("full", "quick", "clean")]
    [string]$Mode = "full"
)

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

function Test-Docker { 
    try { 
        $null = docker ps 2>&1
        return $LASTEXITCODE -eq 0 
    } catch { 
        return $false 
    } 
}

function Start-Docker {
    Log "Starting Docker Desktop..." "Yellow"
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath
        $waitTime = 0
        
        while (-not (Test-Docker) -and $waitTime -lt 60) {
            Log "Waiting for Docker ($waitTime/60s)..." "Cyan"
            Start-Sleep 2
            $waitTime += 2
        }
        
        if (Test-Docker) {
            Log "[OK] Docker started successfully" "Green"
            return $true
        }
    }
    
    Log "[ERROR] Docker failed to start!" "Red"
    return $false
}

# ============================================
# MAIN EXECUTION
# ============================================

Clear-Host

$startTime = Get-Date

Log ""
Log "===========================================================" "Cyan"
Log "         SAAS-IA COMPLETE RESTART                         " "Cyan"
Log "===========================================================" "Cyan"
Log ""
Log "Mode: $Mode | KeepDB: $KeepDB" "Cyan"
Log ""

# Check Docker
if (-not (Test-Docker)) {
    if (-not (Start-Docker)) {
        Log ""
        Log "ERROR: Docker is required but not available." "Red"
        exit 1
    }
} else {
    Log "[OK] Docker is running" "Green"
}

# ============================================
# STOP ALL SERVICES
# ============================================

Step "STOPPING PROCESSES        "

# Stop Frontend (Node.js on port 3002)
Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*SaaS-IA*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Log "  [OK] Stopped Node.js processes (Frontend)" "Cyan"

# Stop Backend (Python)
Get-Process python,uvicorn -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*SaaS-IA*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Log "  [OK] Stopped Python processes (Backend)" "Cyan"

# Stop Docker containers
Push-Location $BACKEND
docker-compose down --remove-orphans 2>&1 | Out-Null
Pop-Location

Log "  [OK] Stopped Docker containers" "Cyan"
Log "[OK] All processes stopped" "Green"

# ============================================
# CLEAN (if not quick mode)
# ============================================

if ($Mode -ne "quick") {
    
    # Clean Backend
    Step "CLEANING BACKEND          "
    
    if (Test-Path $BACKEND) {
        Push-Location $BACKEND
        
        # Clean Python cache
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        
        Get-ChildItem -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | 
            Remove-Item -Force -ErrorAction SilentlyContinue
        
        Get-ChildItem -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        
        Get-ChildItem -Recurse -Directory -Filter ".mypy_cache" -ErrorAction SilentlyContinue | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        
        Get-ChildItem -Recurse -Filter ".coverage*" -ErrorAction SilentlyContinue | 
            Remove-Item -Force -ErrorAction SilentlyContinue
        
        # Clean Alembic cache
        if (Test-Path "alembic\__pycache__") {
            Remove-Item "alembic\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        Pop-Location
        Log "[OK] Backend cleaned" "Green"
    }
    
    # Clean Frontend
    Step "CLEANING FRONTEND         "
    
    if (Test-Path $FRONTEND) {
        Push-Location $FRONTEND
        
        ".next",".vite","node_modules\.cache","dist","build","coverage",".eslintcache" | ForEach-Object {
            if (Test-Path $_) {
                Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
        
        Pop-Location
        Log "[OK] Frontend cleaned" "Green"
    }
    
    # Clean Docker
    Step "CLEANING DOCKER           "
    
    docker container prune -f 2>&1 | Out-Null
    docker network prune -f 2>&1 | Out-Null
    
    if (-not $KeepDB) {
        docker volume prune -f 2>&1 | Out-Null
        Log "[OK] Docker cleaned (including volumes)" "Green"
    } else {
        Log "[OK] Docker cleaned (volumes preserved)" "Green"
    }
    
    docker builder prune -f 2>&1 | Out-Null
}

# ============================================
# EXIT IF CLEAN MODE
# ============================================

if ($Mode -eq "clean") {
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    
    Log ""
    Log "===========================================================" "Green"
    Log "         [OK] SAAS-IA ENVIRONMENT CLEANED                 " "Green"
    Log "===========================================================" "Green"
    Log ""
    Log "[TIME] Completed in $([math]::Round($elapsed, 1))s" "Green"
    Log ""
    Log "To start services: run start-env.bat" "Cyan"
    Log ""
    exit 0
}

# ============================================
# START SERVICES
# ============================================

# Start Docker services
Step "STARTING DOCKER           "

Push-Location $BACKEND

Log "Starting Docker Compose services..." "Cyan"
docker-compose up -d 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Start-Sleep 8
    
    # Check Docker services
    $containers = docker ps --filter "name=saas-ia" --format "{{.Names}}: {{.Status}}"
    
    if ($containers) {
        $containers | ForEach-Object { 
            Log "  [OK] $_" "Green" 
        }
    } else {
        Log "  [WARN] No containers found" "Yellow"
    }
    
    Log "[OK] Docker services ready (PostgreSQL:5435, Redis:6382)" "Green"
} else {
    Log "[ERROR] Failed to start Docker Compose" "Red"
    Pop-Location
    exit 1
}

Pop-Location

# Start Frontend
Step "STARTING FRONTEND         "

Push-Location $FRONTEND

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Log "Installing npm packages (first time only)..." "Yellow"
    $installOutput = npm install 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Log "[ERROR] npm install failed!" "Red"
        Write-Host $installOutput -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Log "[OK] npm packages installed" "Green"
} else {
    Log "[OK] npm packages exist (skipped)" "Green"
}

# Start Frontend on port 3002 (Vite default)
Log "Starting frontend on port 3002..." "Cyan"
Start-Process "pwsh.exe" -ArgumentList "-NoExit","-Command","cd '$FRONTEND'; npm run dev" -WorkingDirectory $FRONTEND

Pop-Location

# Open browser
if (-not $SkipBrowser) {
    Log "[BROWSER] Opening browser..." "Cyan"
    Start-Sleep 3
    Start-Process "http://localhost:3002"
}

# Wait for services
Start-Sleep 3

# Summary
$elapsed = ((Get-Date) - $startTime).TotalSeconds

Log ""
Log "===========================================================" "Green"
Log "         [SUCCESS] SAAS-IA ENVIRONMENT READY!             " "Green"
Log "===========================================================" "Green"
Log ""
Log "Services:" "Cyan"
Log "  Docker:     PostgreSQL:5435, Redis:6382" "White"
Log "  Backend:    http://localhost:8004" "White"
Log "  API Docs:   http://localhost:8004/docs" "White"
Log "  Frontend:   http://localhost:3002" "White"
Log ""
Log "Logs:" "Cyan"
Log "  Backend:   docker-compose logs -f saas-ia-backend" "White"
Log "  Frontend:  Check PowerShell window with vite" "White"
Log ""
Log "[TIME] Restarted in $([math]::Round($elapsed, 1))s" "Green"
Log ""
Log "[TIP] Use stop-env.bat to stop all services" "Yellow"
Log ""

# Attach to backend logs (like WeLAB)
Log ""
Log "===========================================================" "Cyan"
Log "  BACKEND LOGS (Press Ctrl+C to exit, services continue)" "Cyan"
Log "===========================================================" "Cyan"
Log ""
Start-Sleep 2

Push-Location $BACKEND
docker-compose logs -f saas-ia-backend
Pop-Location

