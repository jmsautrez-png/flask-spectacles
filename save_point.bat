@echo off
REM =====================================================
REM Double-clic pour creer un point de restauration Git
REM =====================================================
cd /d "%~dp0"
chcp 65001 >nul
powershell.exe -ExecutionPolicy Bypass -File "%~dp0save_point.ps1"
echo.
pause
