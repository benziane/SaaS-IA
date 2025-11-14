#Requires -Version 5.1
# ============================================
# SaaS-IA Cleanup Ports Script
# Version: 1.0.0
# ============================================

$ErrorActionPreference = "Continue"

function Log($msg, $col="White") { 
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor $col 
}

function Stop-ProcessOnPort {
    param([int]$Port, [string]$ServiceName = "Service")
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        
        if ($connections) {
            $processList = $connections | Select-Object -ExpandProperty OwningProcess -Unique
            
            Log "Found $($processList.Count) process(es) on port $Port" "Yellow"
            
            foreach ($processId in $processList) {
                try {
                    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                    if ($process) {
                        Log "  Stopping $ServiceName (PID: $processId, Name: $($process.Name))..." "Cyan"
                        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                        Start-Sleep -Milliseconds 500
                        Log "  ✅ Process stopped" "Green"
                    }
                } catch {
                    Log "  ⚠️  Could not stop PID $processId" "Yellow"
                }
            }
            
            # Vérifier que le port est bien libéré
            Start-Sleep -Milliseconds 500
            $stillUsed = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
            
            if (-not $stillUsed) {
                Log "✅ Port $Port is now free" "Green"
                return $true
            } else {
                Log "⚠️  Port $Port is still in use" "Yellow"
                return $false
            }
        } else {
            Log "✅ Port $Port is already free" "Green"
            return $true
        }
    } catch {
        Log "Error checking port ${Port}: $($_.Exception.Message)" "Red"
        return $false
    }
}

# ============================================
# MAIN EXECUTION
# ============================================

Clear-Host

Log ""
Log "===========================================================" "Cyan"
Log "         SAAS-IA PORTS CLEANUP                            " "Cyan"
Log "===========================================================" "Cyan"
Log ""

$ports = @(
    @{ Port = 3002; Name = "Frontend (Next.js)" },
    @{ Port = 8004; Name = "Backend (FastAPI)" },
    @{ Port = 5435; Name = "PostgreSQL" },
    @{ Port = 6382; Name = "Redis" }
)

$cleaned = 0
$failed = 0

foreach ($portInfo in $ports) {
    Log ""
    Log "Checking port $($portInfo.Port) - $($portInfo.Name)..." "Magenta"
    
    if (Stop-ProcessOnPort -Port $portInfo.Port -ServiceName $portInfo.Name) {
        $cleaned++
    } else {
        $failed++
    }
}

Log ""
Log "===========================================================" "Cyan"
Log "         CLEANUP COMPLETE                                 " "Cyan"
Log "===========================================================" "Cyan"
Log ""
Log "Cleaned: $cleaned ports" "Green"
if ($failed -gt 0) {
    Log "Failed:  $failed ports" "Red"
}
Log ""

if ($failed -eq 0) {
    Log "✅ All ports are now free!" "Green"
    exit 0
} else {
    Log "⚠️  Some ports could not be cleaned" "Yellow"
    Log "Try running this script as Administrator" "Cyan"
    exit 1
}

