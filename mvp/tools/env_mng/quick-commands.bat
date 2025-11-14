@echo off
REM ============================================
REM SaaS-IA Quick Commands Menu
REM Version: 1.0.0
REM ============================================

:MENU
cls
echo.
echo ================================================================
echo          SAAS-IA ENVIRONMENT - QUICK COMMANDS
echo ================================================================
echo.
echo  1. Start Environment (Full)
echo  2. Stop Environment
echo  3. Restart Environment (Full Clean)
echo  4. Restart Environment (Quick - No Clean)
echo  5. Check Status
echo  6. Check Status (Detailed)
echo  7. View Backend Logs
echo  8. View PostgreSQL Logs
echo  9. View Redis Logs
echo  10. Open Backend (http://localhost:8004)
echo  11. Open API Docs (http://localhost:8004/docs)
echo  12. Open Frontend (http://localhost:3002)
echo  13. Docker Compose Status
echo  14. Clean Only (No Restart)
echo  15. Restart with KeepDB
echo  0. Exit
echo.
echo ================================================================
echo.

set /p choice="Enter your choice (0-15): "

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto RESTART_FULL
if "%choice%"=="4" goto RESTART_QUICK
if "%choice%"=="5" goto CHECK
if "%choice%"=="6" goto CHECK_DETAILED
if "%choice%"=="7" goto LOGS_BACKEND
if "%choice%"=="8" goto LOGS_POSTGRES
if "%choice%"=="9" goto LOGS_REDIS
if "%choice%"=="10" goto OPEN_BACKEND
if "%choice%"=="11" goto OPEN_DOCS
if "%choice%"=="12" goto OPEN_FRONTEND
if "%choice%"=="13" goto DOCKER_STATUS
if "%choice%"=="14" goto CLEAN_ONLY
if "%choice%"=="15" goto RESTART_KEEPDB
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:START
echo.
echo Starting SaaS-IA Environment...
echo.
call "%~dp0start-env.bat"
goto MENU

:STOP
echo.
echo Stopping SaaS-IA Environment...
echo.
call "%~dp0stop-env.bat"
goto MENU

:RESTART_FULL
echo.
echo Restarting SaaS-IA Environment (Full Clean)...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0restart-env.ps1"
pause
goto MENU

:RESTART_QUICK
echo.
echo Restarting SaaS-IA Environment (Quick - No Clean)...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0restart-env.ps1" -Mode quick
pause
goto MENU

:CHECK
echo.
echo Checking SaaS-IA Environment Status...
echo.
call "%~dp0check-status.bat"
goto MENU

:CHECK_DETAILED
echo.
echo Checking SaaS-IA Environment Status (Detailed)...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0check-status.ps1" -Detailed
pause
goto MENU

:LOGS_BACKEND
echo.
echo Viewing Backend Logs (Ctrl+C to exit)...
echo.
cd /d "%~dp0..\..\backend"
docker-compose logs -f backend
pause
goto MENU

:LOGS_POSTGRES
echo.
echo Viewing PostgreSQL Logs (Ctrl+C to exit)...
echo.
cd /d "%~dp0..\..\backend"
docker-compose logs -f db
pause
goto MENU

:LOGS_REDIS
echo.
echo Viewing Redis Logs (Ctrl+C to exit)...
echo.
cd /d "%~dp0..\..\backend"
docker-compose logs -f redis
pause
goto MENU

:OPEN_BACKEND
echo.
echo Opening Backend (http://localhost:8004)...
start http://localhost:8004
timeout /t 2 >nul
goto MENU

:OPEN_DOCS
echo.
echo Opening API Docs (http://localhost:8004/docs)...
start http://localhost:8004/docs
timeout /t 2 >nul
goto MENU

:OPEN_FRONTEND
echo.
echo Opening Frontend (http://localhost:3002)...
start http://localhost:3002
timeout /t 2 >nul
goto MENU

:DOCKER_STATUS
echo.
echo Docker Compose Status:
echo.
cd /d "%~dp0..\..\backend"
docker-compose ps
echo.
pause
goto MENU

:CLEAN_ONLY
echo.
echo Cleaning SaaS-IA Environment (No Restart)...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0restart-env.ps1" -Mode clean
pause
goto MENU

:RESTART_KEEPDB
echo.
echo Restarting SaaS-IA Environment (Keep Database)...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0restart-env.ps1" -KeepDB
pause
goto MENU

:EXIT
echo.
echo Goodbye!
timeout /t 1 >nul
exit

