@echo off
REM ============================================
REM SaaS-IA Environment Status Checker (BAT Launcher)
REM Version: 1.0.0
REM ============================================

powershell.exe -ExecutionPolicy Bypass -File "%~dp0check-status.ps1"

