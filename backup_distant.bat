@echo off
REM ====================================================================
REM Backup distant : PostgreSQL + photos S3 vers Dropbox
REM Double-cliquez sur ce fichier pour lancer un backup manuel.
REM ====================================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python backup_distant.py
echo.
echo ============================================
echo  Backup termine. Appuyez sur une touche...
echo ============================================
pause >nul
