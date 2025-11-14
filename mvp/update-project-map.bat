@echo off
REM Script one-click pour régénérer project-map.json
REM Usage: double-cliquer ou lancer depuis cmd

echo.
echo ========================================
echo   Regeneration du project-map.json
echo ========================================
echo.

cd backend

REM Vérifier si Python est disponible
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Utilisation de Python...
    python scripts\generate_project_map.py
) else (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    echo Installez Python 3.11+ depuis https://www.python.org/
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Generation terminee!
echo ========================================
echo.
echo Fichier genere: project-map.json
echo.
pause

