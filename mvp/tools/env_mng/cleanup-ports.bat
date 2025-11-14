@echo off
REM ============================================
REM SaaS-IA Cleanup Ports Batch Wrapper
REM ============================================

powershell.exe -ExecutionPolicy Bypass -File "%~dp0cleanup-ports.ps1"
pause

