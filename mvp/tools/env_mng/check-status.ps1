#Requires -Version 5.1
# ============================================
# SaaS-IA Environment Status Checker
# Version: 1.0.0 - Ultra-Fast Parallel Checks
# ============================================

param(
    [switch]$Json = $false,
    [switch]$Detailed = $false
)

# Configuration UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Paths
$SAAS_IA_ROOT = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$MVP_ROOT = Join-Path $SAAS_IA_ROOT "mvp"
$BACKEND = Join-Path $MVP_ROOT "backend"
$FRONTEND = Join-Path $MVP_ROOT "frontend"

# Global state
$script:FailedServices = @()
$script:StartTime = Get-Date

# ============================================
# HELPER FUNCTIONS
# ============================================

function Log($msg, $col="White") { 
    if (-not $Json) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor $col 
    }
}

function Step($msg, $col="Cyan") { 
    if (-not $Json) {
        Log "`n========== $msg ==========" $col
    }
}

function Write-ServiceStatus {
    param(
        [string]$Service,
        [string]$Status,
        [string]$Details = ""
    )
    
    if ($Json) { return }
    
    $statusColor = switch ($Status) {
        "OK" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "INACTIVE" { "Gray" }
        default { "White" }
    }
    
    $statusIcon = switch ($Status) {
        "OK" { "[OK]" }
        "ERROR" { "[ERROR]" }
        "WARNING" { "[WARN]" }
        "INACTIVE" { "[OFF]" }
        default { "[?]" }
    }
    
    $padding = " " * (20 - $Service.Length)
    
    if ($Details) {
        Write-Host "   $statusIcon $Service$padding : " -NoNewline -ForegroundColor $statusColor
        Write-Host $Details -ForegroundColor Gray
    } else {
        Write-Host "   $statusIcon $Service$padding : $Status" -ForegroundColor $statusColor
    }
}

# ============================================
# ULTRA-FAST PARALLEL SERVICE CHECKS
# ============================================

function Get-AllServicesStatus {
    $jobs = @()
    
    # Job 1: Backend (FastAPI in Docker)
    $jobs += @{
        Job = Start-Job -ScriptBlock {
            param($Port)
            $result = @{Status = "INACTIVE"; Port = $Port}
            
            try {
                # Check if port is listening
                $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
                
                if ($connection) {
                    # HTTP Health Check
                    $httpOk = $false
                    $responseTime = 0
                    
                    try {
                        $sw = [System.Diagnostics.Stopwatch]::StartNew()
                        $response = Invoke-WebRequest -Uri "http://localhost:$Port/health" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
                        $sw.Stop()
                        $responseTime = $sw.ElapsedMilliseconds
                        $httpOk = $response.StatusCode -eq 200
                    } catch {}
                    
                    $result = @{
                        Status = if ($httpOk) { "OK" } else { "WARNING" }
                        Port = $Port
                        HttpHealth = $httpOk
                        ResponseTime = $responseTime
                    }
                }
            } catch {}
            
            return $result
        } -ArgumentList 8004
        Name = "Backend"
        Critical = $true
    }
    
    # Job 2: Frontend (Next.js)
    $jobs += @{
        Job = Start-Job -ScriptBlock {
            param($Port)
            $result = @{Status = "INACTIVE"; Port = $Port}
            
            try {
                $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
                
                if ($connection) {
                    $processId = $connection[0].OwningProcess
                    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                    
                    $result = @{
                        Status = "OK"
                        Port = $Port
                        PID = $processId
                        ProcessName = $process.ProcessName
                        Memory = [math]::Round($process.WorkingSet64 / 1MB, 0)
                        Uptime = (Get-Date) - $process.StartTime
                    }
                }
            } catch {}
            
            return $result
        } -ArgumentList 3002
        Name = "Frontend"
        Critical = $true
    }
    
    # Job 3: PostgreSQL
    $jobs += @{
        Job = Start-Job -ScriptBlock {
            param($Port)
            $result = @{Status = "INACTIVE"; Port = $Port}
            
            try {
                $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
                
                if ($connection) {
                    # Check if PostgreSQL is ready
                    $ready = $false
                    
                    try {
                        $pgCheck = docker exec saas-ia-mvp-db pg_isready -U aiuser -d ai_saas 2>$null
                        $ready = $pgCheck -match "accepting connections"
                    } catch {}
                    
                    $result = @{
                        Status = if ($ready) { "OK" } else { "WARNING" }
                        Port = $Port
                        Ready = $ready
                        Container = "saas-ia-mvp-db"
                    }
                }
            } catch {}
            
            return $result
        } -ArgumentList 5435
        Name = "PostgreSQL"
        Critical = $true
    }
    
    # Job 4: Redis
    $jobs += @{
        Job = Start-Job -ScriptBlock {
            param($Port)
            $result = @{Status = "INACTIVE"; Port = $Port}
            
            try {
                $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
                
                if ($connection) {
                    # Check if Redis is ready
                    $ready = $false
                    
                    try {
                        $redisCheck = docker exec saas-ia-mvp-redis redis-cli ping 2>$null
                        $ready = $redisCheck -match "PONG"
                    } catch {}
                    
                    $result = @{
                        Status = if ($ready) { "OK" } else { "WARNING" }
                        Port = $Port
                        Ready = $ready
                        Container = "saas-ia-mvp-redis"
                    }
                }
            } catch {}
            
            return $result
        } -ArgumentList 6382
        Name = "Redis"
        Critical = $true
    }
    
    # Job 5: Docker
    $jobs += @{
        Job = Start-Job -ScriptBlock {
            $result = @{Status = "INACTIVE"}
            
            try {
                $null = docker ps 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    $version = docker version --format "{{.Server.Version}}" 2>$null
                    $containers = docker ps --filter "name=saas-ia-mvp" --format "{{.Names}}:{{.Status}}" 2>$null
                    $running = ($containers | Measure-Object).Count
                    
                    $result = @{
                        Status = "OK"
                        Version = $version
                        Containers = $containers
                        RunningCount = $running
                    }
                }
            } catch {}
            
            return $result
        }
        Name = "Docker"
        Critical = $true
    }
    
    # Wait for all jobs and collect results
    $results = @{}
    
    foreach ($jobInfo in $jobs) {
        $result = Receive-Job -Job $jobInfo.Job -Wait -ErrorAction SilentlyContinue
        Remove-Job -Job $jobInfo.Job -Force -ErrorAction SilentlyContinue
        
        $results[$jobInfo.Name] = @{
            Result = $result
            Critical = $jobInfo.Critical
        }
    }
    
    return $results
}

# ============================================
# DISPLAY FUNCTIONS
# ============================================

function Show-Results {
    param($Results)
    
    # Header
    Log ""
    Log "===========================================================" "Cyan"
    Log "         SAAS-IA ENVIRONMENT STATUS                       " "Cyan"
    Log "===========================================================" "Cyan"
    Log ""
    
    # Core Services
    Step "CORE SERVICES" "Yellow"
    
    # Backend
    $backend = $Results["Backend"].Result
    if ($backend.Status -eq "OK") {
        $health = if ($backend.HttpHealth) { "Health [OK]" } else { "Health [N/A]" }
        $details = "Port $($backend.Port) | $health | Response $($backend.ResponseTime)ms"
        Write-ServiceStatus "Backend (FastAPI)" "OK" $details
    } elseif ($backend.Status -eq "WARNING") {
        Write-ServiceStatus "Backend (FastAPI)" "WARNING" "Port open but health check failed"
        $script:FailedServices += "Backend"
    } else {
        Write-ServiceStatus "Backend (FastAPI)" "INACTIVE" "Port 8004 not listening"
        $script:FailedServices += "Backend"
    }
    
    # Frontend
    $frontend = $Results["Frontend"].Result
    if ($frontend.Status -eq "OK") {
        $uptime = "{0:hh\:mm\:ss}" -f $frontend.Uptime
        $details = "Port $($frontend.Port) | PID $($frontend.PID) | RAM $($frontend.Memory)MB | Uptime $uptime"
        Write-ServiceStatus "Frontend (Next.js)" "OK" $details
    } else {
        Write-ServiceStatus "Frontend (Next.js)" "INACTIVE" "Port 3002 not listening"
        $script:FailedServices += "Frontend"
    }
    
    Log ""
    Step "DATABASE SERVICES" "Yellow"
    
    # PostgreSQL
    $postgres = $Results["PostgreSQL"].Result
    if ($postgres.Status -eq "OK") {
        Write-ServiceStatus "PostgreSQL" "OK" "Port $($postgres.Port) | Ready [OK] | Container: $($postgres.Container)"
    } elseif ($postgres.Status -eq "WARNING") {
        Write-ServiceStatus "PostgreSQL" "WARNING" "Port open but not ready"
        $script:FailedServices += "PostgreSQL"
    } else {
        Write-ServiceStatus "PostgreSQL" "INACTIVE" "Port 5435 not listening"
        $script:FailedServices += "PostgreSQL"
    }
    
    # Redis
    $redis = $Results["Redis"].Result
    if ($redis.Status -eq "OK") {
        Write-ServiceStatus "Redis" "OK" "Port $($redis.Port) | Ready [OK] | Container: $($redis.Container)"
    } elseif ($redis.Status -eq "WARNING") {
        Write-ServiceStatus "Redis" "WARNING" "Port open but not ready"
        $script:FailedServices += "Redis"
    } else {
        Write-ServiceStatus "Redis" "INACTIVE" "Port 6382 not listening"
        $script:FailedServices += "Redis"
    }
    
    Log ""
    Step "INFRASTRUCTURE" "Yellow"
    
    # Docker
    $docker = $Results["Docker"].Result
    if ($docker.Status -eq "OK") {
        Write-ServiceStatus "Docker Desktop" "OK" "Version $($docker.Version) | $($docker.RunningCount) containers running"
        
        if ($Detailed -and $docker.Containers) {
            Log "   Containers:" "Gray"
            foreach ($container in $docker.Containers) {
                $parts = $container -split ":"
                Log "     • $($parts[0]): $($parts[1])" "Gray"
            }
        }
    } else {
        Write-ServiceStatus "Docker Desktop" "INACTIVE" "Docker not available"
        $script:FailedServices += "Docker"
    }
    
    # Summary
    Log ""
    Log "===========================================================" "Cyan"
    
    $elapsed = ((Get-Date) - $script:StartTime).TotalMilliseconds
    
    if ($script:FailedServices.Count -eq 0) {
        Log "   [SUCCESS] ALL CRITICAL SERVICES ARE UP" "Green"
        Log "===========================================================" "Cyan"
        Log ""
        Log "Quick Access:" "White"
        Log "   - Backend:    http://localhost:8004" "Cyan"
        Log "   - API Docs:   http://localhost:8004/docs" "Cyan"
        Log "   - Frontend:   http://localhost:3002" "Cyan"
        Log "   - PostgreSQL: localhost:5435" "Cyan"
        Log "   - Redis:      localhost:6382" "Cyan"
        Log ""
        Log "[FAST] Status check completed in $([math]::Round($elapsed, 0))ms" "Green"
    } else {
        Log "   [ERROR] CRITICAL SERVICES DOWN" "Red"
        Log "===========================================================" "Cyan"
        Log ""
        Log "Failed Services:" "Red"
        foreach ($service in $script:FailedServices) {
            Log "   - $service" "Red"
        }
        Log ""
        Log "Solution:" "Yellow"
        Log "   1. Run: restart-env.bat" "Cyan"
        Log "   2. Wait 30 seconds" "Cyan"
        Log "   3. Run: check-status.bat" "Cyan"
        Log ""
        Log "[FAST] Status check completed in $([math]::Round($elapsed, 0))ms" "Yellow"
    }
}

function Export-JsonResults {
    param($Results)
    
    $output = @{
        timestamp = (Get-Date).ToString("o")
        elapsed_ms = ((Get-Date) - $script:StartTime).TotalMilliseconds
        status = if ($script:FailedServices.Count -eq 0) { "healthy" } else { "unhealthy" }
        failed_services = $script:FailedServices
        services = @{}
    }
    
    foreach ($key in $Results.Keys) {
        $output.services[$key] = $Results[$key].Result
    }
    
    $output | ConvertTo-Json -Depth 10
}

# ============================================
# MAIN EXECUTION
# ============================================

if (-not $Json) {
    Clear-Host
}

# Run parallel checks
$results = Get-AllServicesStatus

# Display or export results
if ($Json) {
    Export-JsonResults $results
} else {
    Show-Results $results
    
    Log ""
    Log "Press any key to exit..." "Gray"
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

exit $(if ($script:FailedServices.Count -eq 0) { 0 } else { 1 })

