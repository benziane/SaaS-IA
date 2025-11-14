# ============================================
# Fix Metadata Warnings - Next.js 15
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  FIX METADATA WARNINGS - NEXT.JS 15" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Stop frontend if running
Write-Host "[1/4] Stopping frontend..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like "*next dev*" -or $_.CommandLine -like "*:3002*" 
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Write-Host "  [OK] Frontend stopped" -ForegroundColor Green

# Clean Next.js cache
Write-Host ""
Write-Host "[2/4] Cleaning Next.js cache..." -ForegroundColor Yellow
if (Test-Path ".next") {
    Remove-Item -Recurse -Force ".next"
    Write-Host "  [OK] .next directory removed" -ForegroundColor Green
}
if (Test-Path "node_modules/.cache") {
    Remove-Item -Recurse -Force "node_modules/.cache"
    Write-Host "  [OK] node_modules/.cache removed" -ForegroundColor Green
}

# Remove metadata exports from client components
Write-Host ""
Write-Host "[3/4] Removing metadata from client components..." -ForegroundColor Yellow

$files = @(
    "src\app\(auth)\login\page.tsx",
    "src\app\(auth)\register\page.tsx",
    "src\app\(dashboard)\dashboard\page.tsx",
    "src\app\(dashboard)\transcription\page.tsx"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        
        # Check if file has 'use client' and metadata export
        if ($content -match "'use client'" -and $content -match "export const metadata") {
            Write-Host "  [WARN] $file has metadata in client component (will be removed)" -ForegroundColor Yellow
            
            # Remove metadata export block
            $content = $content -replace "(?s)export const metadata.*?};", ""
            
            # Remove Metadata import if exists
            $content = $content -replace ",?\s*Metadata\s*,?", ""
            $content = $content -replace "import type \{\s*\} from 'next';", ""
            
            # Save
            $content | Set-Content $file -NoNewline
            Write-Host "  [OK] Cleaned $file" -ForegroundColor Green
        } else {
            Write-Host "  [SKIP] $file (no metadata or not client component)" -ForegroundColor Gray
        }
    }
}

# Restart frontend
Write-Host ""
Write-Host "[4/4] Restarting frontend..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
Start-Sleep 3
Write-Host "  [OK] Frontend restarted on port 3002" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DONE! Check browser: http://localhost:3002" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Warnings should be gone now!" -ForegroundColor Yellow
Write-Host ""

