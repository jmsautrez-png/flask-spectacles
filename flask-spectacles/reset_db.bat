@echo off
cd /d %~dp0
if exist instance\app.db (
  del /f /q instance\app.db
  echo Base supprimee. Elle sera recrée au prochain demarrage.
) else (
  echo Aucune base a supprimer (instance\app.db introuvable).
)
pause
