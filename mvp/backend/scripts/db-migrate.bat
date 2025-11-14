@echo off
REM Database Migration Script - Grade S++
REM Usage: scripts\db-migrate.bat [command] [args]

setlocal enabledelayedexpansion

REM Check command
if "%1"=="" goto usage

if "%1"=="generate" goto generate
if "%1"=="upgrade" goto upgrade
if "%1"=="downgrade" goto downgrade
if "%1"=="current" goto current
if "%1"=="history" goto history
if "%1"=="reset" goto reset
goto usage

:generate
if "%2"=="" (
    echo [ERROR] Please provide a migration message
    echo Usage: scripts\db-migrate.bat generate "migration message"
    exit /b 1
)
echo.
echo ==================================================
echo   Generate Migration: %~2
echo ==================================================
echo.
alembic revision --autogenerate -m "%~2"
echo.
echo [SUCCESS] Migration generated
echo [WARNING] Please review the migration file before applying!
goto end

:upgrade
echo.
echo ==================================================
echo   Apply Migrations
echo ==================================================
echo.
alembic upgrade head
echo.
echo [SUCCESS] Migrations applied
goto end

:downgrade
set STEPS=%2
if "%STEPS%"=="" set STEPS=-1
echo.
echo ==================================================
echo   Rollback Migrations
echo ==================================================
echo.
echo [WARNING] Rolling back %STEPS% migration(s)
alembic downgrade %STEPS%
echo.
echo [SUCCESS] Rollback completed
goto end

:current
echo.
echo ==================================================
echo   Current Migration
echo ==================================================
echo.
alembic current
goto end

:history
echo.
echo ==================================================
echo   Migration History
echo ==================================================
echo.
alembic history --verbose
goto end

:reset
echo.
echo ==================================================
echo   Reset Database
echo ==================================================
echo.
echo [WARNING] This will drop all tables and reapply migrations
set /p confirm="Are you sure? (yes/no): "
if /i "%confirm%"=="yes" (
    alembic downgrade base
    alembic upgrade head
    echo.
    echo [SUCCESS] Database reset completed
) else (
    echo.
    echo [ERROR] Reset cancelled
)
goto end

:usage
echo Database Migration Tool - SaaS-IA MVP
echo.
echo Usage: scripts\db-migrate.bat [command] [args]
echo.
echo Commands:
echo   generate "message"    Generate new migration
echo   upgrade               Apply all pending migrations
echo   downgrade [-1]        Rollback migrations (default: -1)
echo   current               Show current migration
echo   history               Show migration history
echo   reset                 Reset database (downgrade + upgrade)
echo.
echo Examples:
echo   scripts\db-migrate.bat generate "add user table"
echo   scripts\db-migrate.bat upgrade
echo   scripts\db-migrate.bat downgrade -1
goto end

:end
endlocal

