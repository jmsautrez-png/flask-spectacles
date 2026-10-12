@echo off
setlocal
REM ====================================================================
REM Backup distant : PostgreSQL + photos S3 vers Dropbox
REM Double-cliquez sur ce fichier pour lancer un backup manuel.
REM ====================================================================
cd /d "%~dp0"
set "PYTHON_EXE=%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\Local\flask-spectacles-backup\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [ERREUR] Environnement Python de sauvegarde introuvable :
    echo %PYTHON_EXE%
    exit /b 1
)
set "PYTHONUTF8=1"
if /I "%~1"=="--scheduled" goto scheduled
"%PYTHON_EXE%" backup_distant.py
set "RESULT=%ERRORLEVEL%"
echo.
echo ============================================
echo  Backup termine. Appuyez sur une touche...
echo ============================================
pause >nul
exit /b %RESULT%

:scheduled
"%PYTHON_EXE%" backup_distant.py >> "%LOCALAPPDATA%\flask-spectacles-backup-scheduled.log" 2>&1
exit /b %ERRORLEVEL%
