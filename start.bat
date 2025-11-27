@echo off
title Demarrage - AnimatoSpectacle
cd /d %~dp0

if not exist .venv (
  echo [*] Creation de l'environnement virtuel...
  py -m venv .venv
)

echo [*] Activation de l'environnement...
call .venv\Scripts\activate

echo [*] Installation des dependances...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [*] Demarrage de l'appli (http://127.0.0.1:5000)...
set FLASK_DEBUG=True
set FLASK_APP=wsgi:app
python -m flask run

echo.
echo [FIN] App fermee. Appuyez sur une touche pour sortir.
pause >nul
