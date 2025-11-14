# Script PowerShell pour vérifier les ports utilisés par les projets
# Usage: .\check-ports.ps1

Write-Host "🔍 Vérification des ports utilisés par les projets..." -ForegroundColor Cyan
Write-Host ""

# Définir les chemins des projets
$projectsRoot = "C:\Users\ibzpc\Git"
$labSaasRoot = "C:\Users\ibzpc\lab-saas"

$allProjects = @(
    @{Name="WeLAB"; Path="$projectsRoot\WeLAB"},
    @{Name="LabSaaS"; Path=$labSaasRoot},
    @{Name="Design"; Path="$projectsRoot\design"},
    @{Name="Provisioning"; Path="$projectsRoot\provisioning"},
    @{Name="Sifate-Voyage"; Path="$projectsRoot\sifate-voyage"},
    @{Name="Markdown-Viewer"; Path="$projectsRoot\markdown-viewer"},
    @{Name="SaaS-IA"; Path="$projectsRoot\SaaS-IA"}
)

# Ports à vérifier (patterns communs)
$portPatterns = @(
    @{Pattern='port:\s*"?(\d+)"?'; Description="Docker Compose port"},
    @{Pattern='PORT=(\d+)'; Description=".env PORT"},
    @{Pattern='localhost:(\d+)'; Description="localhost URL"},
    @{Pattern=':\s*(\d+)\s*/tcp'; Description="Docker port mapping"},
    @{Pattern='--port\s+(\d+)'; Description="Command line port"},
    @{Pattern='"port":\s*(\d+)'; Description="JSON port config"},
    @{Pattern='VITE_PORT=(\d+)'; Description="Vite port"},
    @{Pattern='NEXT_PUBLIC.*PORT.*=(\d+)'; Description="Next.js port"}
)

# Fichiers à scanner
$fileExtensions = @("*.yml", "*.yaml", "*.env*", "*.json", "*.toml", "*.py", "*.js", "*.ts", "*.tsx", "*.md", "Dockerfile*")

# Stocker tous les ports trouvés
$allPorts = @{}

foreach ($project in $allProjects) {
    if (Test-Path $project.Path) {
        Write-Host "📂 Scan de $($project.Name)..." -ForegroundColor Yellow
        
        $projectPorts = @()
        
        foreach ($ext in $fileExtensions) {
            $files = Get-ChildItem -Path $project.Path -Filter $ext -Recurse -ErrorAction SilentlyContinue | 
                     Where-Object { $_.FullName -notmatch 'node_modules|\.git|\.venv|venv|__pycache__|dist|build' }
            
            foreach ($file in $files) {
                try {
                    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
                    
                    foreach ($portPattern in $portPatterns) {
                        $matches = [regex]::Matches($content, $portPattern.Pattern)
                        
                        foreach ($match in $matches) {
                            if ($match.Groups.Count -gt 1) {
                                $port = $match.Groups[1].Value
                                
                                # Filtrer les ports valides (1024-65535)
                                if ([int]$port -ge 1024 -and [int]$port -le 65535) {
                                    $portInfo = @{
                                        Port = [int]$port
                                        File = $file.Name
                                        Path = $file.FullName.Replace($project.Path, "")
                                        Type = $portPattern.Description
                                    }
                                    
                                    $projectPorts += $portInfo
                                }
                            }
                        }
                    }
                } catch {
                    # Ignorer les erreurs de lecture de fichiers
                }
            }
        }
        
        # Dédupliquer et trier les ports
        $uniquePorts = $projectPorts | Sort-Object -Property Port -Unique
        
        if ($uniquePorts.Count -gt 0) {
            $allPorts[$project.Name] = $uniquePorts
            
            Write-Host "  ✅ Trouvé $($uniquePorts.Count) port(s)" -ForegroundColor Green
            foreach ($portInfo in ($uniquePorts | Sort-Object Port)) {
                Write-Host "     • Port $($portInfo.Port) - $($portInfo.File) ($($portInfo.Type))" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ℹ️  Aucun port trouvé" -ForegroundColor Gray
        }
        
        Write-Host ""
    } else {
        Write-Host "  ⚠️  Projet non trouvé: $($project.Path)" -ForegroundColor DarkYellow
        Write-Host ""
    }
}

# Résumé global
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📊 RÉSUMÉ GLOBAL DES PORTS UTILISÉS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Créer une liste plate de tous les ports
$flatPorts = @()
foreach ($project in $allPorts.Keys) {
    foreach ($portInfo in $allPorts[$project]) {
        $flatPorts += @{
            Project = $project
            Port = $portInfo.Port
            File = $portInfo.File
        }
    }
}

# Grouper par port pour détecter les conflits
$portGroups = $flatPorts | Group-Object -Property Port | Sort-Object -Property Name

foreach ($group in $portGroups) {
    $port = $group.Name
    $projects = $group.Group | Select-Object -ExpandProperty Project -Unique
    
    if ($projects.Count -gt 1) {
        Write-Host "⚠️  Port $port - CONFLIT POTENTIEL" -ForegroundColor Red
        foreach ($proj in $projects) {
            Write-Host "     └─ $proj" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✅ Port $port - $($projects[0])" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "💡 PORTS DISPONIBLES RECOMMANDÉS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Trouver des ports disponibles dans des plages courantes
$commonRanges = @(
    @{Start=3000; End=3100; Name="Frontend (3000-3100)"},
    @{Start=5000; End=5200; Name="Frontend Alt (5000-5200)"},
    @{Start=8000; End=8100; Name="Backend (8000-8100)"},
    @{Start=9000; End=9100; Name="Services (9000-9100)"}
)

$usedPorts = $flatPorts | Select-Object -ExpandProperty Port | Sort-Object -Unique

foreach ($range in $commonRanges) {
    $availablePorts = @()
    
    for ($p = $range.Start; $p -le $range.End; $p++) {
        if ($usedPorts -notcontains $p) {
            $availablePorts += $p
        }
    }
    
    if ($availablePorts.Count -gt 0) {
        $firstFive = $availablePorts | Select-Object -First 5
        Write-Host "🔓 $($range.Name): " -NoNewline -ForegroundColor Green
        Write-Host ($firstFive -join ", ") -ForegroundColor White
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📝 EXPORT DES RÉSULTATS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Exporter en JSON
$exportPath = Join-Path $PSScriptRoot "ports-usage.json"
$exportData = @{
    ScanDate = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Projects = $allPorts
    Conflicts = @()
    AvailablePorts = @{}
}

# Détecter les conflits
foreach ($group in $portGroups) {
    if ($group.Group.Count -gt 1) {
        $exportData.Conflicts += @{
            Port = [int]$group.Name
            Projects = ($group.Group | Select-Object -ExpandProperty Project -Unique)
        }
    }
}

# Ports disponibles
foreach ($range in $commonRanges) {
    $availablePorts = @()
    for ($p = $range.Start; $p -le $range.End; $p++) {
        if ($usedPorts -notcontains $p) {
            $availablePorts += $p
        }
    }
    $exportData.AvailablePorts[$range.Name] = $availablePorts
}

$exportData | ConvertTo-Json -Depth 10 | Out-File -FilePath $exportPath -Encoding UTF8
Write-Host "✅ Résultats exportés: $exportPath" -ForegroundColor Green

# Exporter en CSV
$csvPath = Join-Path $PSScriptRoot "ports-usage.csv"
$csvData = @()
foreach ($proj in $flatPorts) {
    $csvData += [PSCustomObject]@{
        Project = $proj.Project
        Port = $proj.Port
        File = $proj.File
    }
}
$csvData | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "✅ CSV exporté: $csvPath" -ForegroundColor Green

Write-Host ""
Write-Host "✨ Scan terminé!" -ForegroundColor Cyan

