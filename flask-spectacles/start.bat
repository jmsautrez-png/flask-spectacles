@echo off
title Demarrage - La Selection d'Artemisia
cd /d %~dp0

if not exist .venv (
  echo [*] Creation de l'environnement virtuel...
  py -m venv .venv
)

echo [*] Activation de l'environnement...
call .venv\Scripts\activate

echo [*] Installation des dependances...
pip install --upgrade pip
pip install -r requirements.txt

echo [*] Demarrage de l'appli (http://127.0.0.1:5000)...
python app.py

echo.
echo [FIN] App fermee. Appuyez sur une touche pour sortir.
pause >nul
