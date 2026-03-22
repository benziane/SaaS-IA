# ============================================================
# Script: rebuild-backend.ps1
# Description: Rebuild Backend Docker Image & Restart Services
# ============================================================

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================
# MAIN SCRIPT
# ============================================================

Write-Header "REBUILD BACKEND DOCKER IMAGE"

# Change to project root
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot
Write-Log "Project root: $projectRoot" "Green"

# Step 1: Stop running containers
Write-Log "Stopping running containers..." "Yellow"
try {
    docker-compose down
    Write-Log "Containers stopped successfully" "Green"
} catch {
    Write-Log "Warning: Could not stop containers (they may not be running)" "Yellow"
}

# Step 2: Rebuild backend image
Write-Log "Rebuilding backend image (this may take 2-3 minutes)..." "Yellow"
try {
    docker-compose build backend --no-cache
    Write-Log "Backend image rebuilt successfully" "Green"
} catch {
    Write-Log "ERROR: Failed to rebuild backend image" "Red"
    Write-Log $_.Exception.Message "Red"
    exit 1
}

# Step 3: Start services
Write-Log "Starting services..." "Yellow"
try {
    docker-compose up -d
    Write-Log "Services started successfully" "Green"
} catch {
    Write-Log "ERROR: Failed to start services" "Red"
    Write-Log $_.Exception.Message "Red"
    exit 1
}

# Step 4: Wait for backend to be ready
Write-Log "Waiting for backend to be ready (max 30 seconds)..." "Yellow"
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    $attempt++
    Start-Sleep -Seconds 1
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Log "Backend is ready!" "Green"
        }
    } catch {
        Write-Host "." -NoNewline
    }
}

Write-Host ""

if (-not $backendReady) {
    Write-Log "WARNING: Backend did not respond after 30 seconds" "Yellow"
    Write-Log "Check logs with: docker-compose logs backend" "Yellow"
} else {
    Write-Log "Backend is healthy and ready to accept requests" "Green"
}

# Step 5: Show running containers
Write-Log "Running containers:" "Cyan"
docker-compose ps

Write-Header "REBUILD COMPLETE"

Write-Log "Backend URL: http://localhost:8004" "Green"
Write-Log "Frontend URL: http://localhost:5174" "Green"
Write-Log "Docs: http://localhost:8004/docs" "Green"
Write-Log "" "White"
Write-Log "To view logs: docker-compose logs -f backend" "Yellow"
Write-Log "To stop: docker-compose down" "Yellow"

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

