@echo off
REM Script batch pour lancer le scan des ports
REM Usage: double-cliquer ou lancer depuis cmd

echo.
echo ========================================
echo   Scan des ports utilises par les projets
echo ========================================
echo.

REM Vérifier si PowerShell est disponible
where pwsh >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Utilisation de PowerShell Core...
    pwsh -ExecutionPolicy Bypass -File "%~dp0check-ports.ps1"
) else (
    echo Utilisation de Windows PowerShell...
    powershell -ExecutionPolicy Bypass -File "%~dp0check-ports.ps1"
)

echo.
echo ========================================
echo   Scan termine!
echo ========================================
echo.
pause

