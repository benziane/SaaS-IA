#Requires -Version 5.1
# ============================================
# SaaS-IA Environment Start Script
# Version: 1.0.0
# ============================================

param(
    [switch]$SkipBrowser = $false,
    [switch]$BackendOnly = $false,
    [switch]$FrontendOnly = $false
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

function Test-Port {
    param([int]$Port)
    
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        return $connection -ne $null
    } catch {
        return $false
    }
}

# ============================================
# MAIN EXECUTION
# ============================================

Clear-Host

$startTime = Get-Date

Log ""
Log "===========================================================" "Cyan"
Log "         SAAS-IA ENVIRONMENT - START                      " "Cyan"
Log "===========================================================" "Cyan"
Log ""

# Check Docker
if (-not (Test-Docker)) {
    if (-not (Start-Docker)) {
        Log ""
        Log "ERROR: Docker is required but not available." "Red"
        Log "Please start Docker Desktop manually and try again." "Yellow"
        Log ""
        pause
        exit 1
    }
} else {
    Log "[OK] Docker is running" "Green"
}

# Start Backend (Docker Compose)
if (-not $FrontendOnly) {
    Step "STARTING BACKEND (DOCKER)  "
    
    Push-Location $BACKEND
    
    # Check if already running
    if (Test-Port 8004) {
        Log "[WARN] Backend already running on port 8004" "Yellow"
        Log "Run stop-env.bat first to restart" "Cyan"
    } else {
        Log "Starting Docker Compose services..." "Cyan"
        docker-compose up -d 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Log "Waiting for services to be ready..." "Cyan"
            Start-Sleep 8
            
            # Verify containers (simple check)
            try {
                $psOutput = docker-compose ps 2>&1 | Out-String
                if ($psOutput -match "Up" -or $psOutput -match "running") {
                    Log "[OK] Backend:    http://localhost:8004" "Green"
                    Log "[OK] API Docs:   http://localhost:8004/docs" "Green"
                    Log "[OK] PostgreSQL: localhost:5435" "Green"
                    Log "[OK] Redis:      localhost:6382" "Green"
                } else {
                    Log "[WARN] Docker containers started but verification unclear" "Yellow"
                    Log "[INFO] Check manually: docker-compose ps" "Cyan"
                }
            } catch {
                Log "[WARN] Could not verify containers status" "Yellow"
            }
        } else {
            Log "[ERROR] Failed to start Docker Compose" "Red"
            Pop-Location
            pause
            exit 1
        }
    }
    
    Pop-Location
}

# Start Frontend
if (-not $BackendOnly) {
    Step "STARTING FRONTEND         "
    
    Push-Location $FRONTEND
    
    # Check if already running
    if (Test-Port 3002) {
        Log "[WARN] Frontend already running on port 3002" "Yellow"
        Log "Run stop-env.bat first to restart" "Cyan"
    } else {
        # Check if node_modules exists (simple check like WeLAB)
        if (-not (Test-Path "node_modules")) {
            Log "Installing npm packages (first time only)..." "Yellow"
            $result = npm install 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Log "[ERROR] npm install failed!" "Red"
                Write-Host $result -ForegroundColor Red
                Pop-Location
                pause
                exit 1
            }
            
            Log "[OK] npm packages installed" "Green"
        } else {
            Log "[OK] npm packages exist (skipped)" "Green"
        }
        
        # Start Frontend on port 3002 (SaaS-IA dedicated port)
        Log "Starting frontend on port 3002..." "Cyan"
        Start-Process "pwsh.exe" -ArgumentList "-NoExit","-Command","cd '$FRONTEND'; npm run dev -- --port 3002" -WorkingDirectory $FRONTEND
        
        Start-Sleep 3
        Log "[OK] Frontend:   http://localhost:3002" "Green"
        
        # Open browser
        if (-not $SkipBrowser) {
            Log "Opening browser..." "Cyan"
            Start-Sleep 2
            Start-Process "http://localhost:3002"
        }
    }
    
    Pop-Location
}

# Summary
$elapsed = ((Get-Date) - $startTime).TotalSeconds

Log ""
Log "===========================================================" "Green"
Log "         [SUCCESS] SAAS-IA ENVIRONMENT READY!             " "Green"
Log "===========================================================" "Green"
Log ""

if (-not $FrontendOnly) {
    Log "Backend Services:" "Cyan"
    Log "  PostgreSQL: localhost:5435" "White"
    Log "  Redis:      localhost:6382" "White"
    Log "  Backend:    http://localhost:8004" "White"
    Log "  API Docs:   http://localhost:8004/docs" "White"
}

if (-not $BackendOnly) {
    Log ""
    Log "Frontend:" "Cyan"
    Log "  App:        http://localhost:3002" "White"
}

Log ""
Log "Logs:" "Cyan"
if (-not $FrontendOnly) {
    Log "  Backend:   docker-compose logs -f saas-ia-backend" "White"
}
if (-not $BackendOnly) {
    Log "  Frontend:  Check PowerShell window with vite" "White"
}

Log ""
Log "[TIME] Started in $([math]::Round($elapsed, 1))s" "Green"
Log ""
Log "[TIP] Use stop-env.bat to stop all services" "Yellow"
Log ""

# Attach to backend logs (like WeLAB)
if (-not $FrontendOnly -and -not $BackendOnly) {
    Log ""
    Log "===========================================================" "Cyan"
    Log "  BACKEND LOGS (Press Ctrl+C to exit, services continue)" "Cyan"
    Log "===========================================================" "Cyan"
    Log ""
    Start-Sleep 2
    
    Push-Location $BACKEND
    docker-compose logs -f saas-ia-backend
    Pop-Location
}
