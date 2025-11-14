@echo off
REM ============================================
REM SaaS-IA Environment Stop Script (BAT Launcher)
REM Version: 1.0.0
REM ============================================

powershell.exe -ExecutionPolicy Bypass -File "%~dp0stop-env.ps1"
pause

