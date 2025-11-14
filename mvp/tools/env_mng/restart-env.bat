@echo off
REM ============================================
REM SaaS-IA Environment Restart Script (BAT Launcher)
REM Version: 1.0.0
REM ============================================

powershell.exe -ExecutionPolicy Bypass -File "%~dp0restart-env.ps1"
pause

