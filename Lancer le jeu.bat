@echo off
cd /d "%~dp0"

rem "python" d'abord, sinon le lanceur "py" (installe par python.org meme sans PATH)
set "PY=python"
%PY% --version >nul 2>&1
if errorlevel 1 set "PY=py -3"
%PY% --version >nul 2>&1
if errorlevel 1 (
  echo Python n'est pas installe.
  echo Installe-le depuis https://www.python.org/downloads/ puis relance ce fichier.
  pause
  exit /b 1
)

%PY% -c "import numpy" >nul 2>&1
if errorlevel 1 (
  echo Premiere fois : installation de numpy...
  %PY% -m pip install --user -r requirements.txt
)

%PY% riemann_jeu.py
if errorlevel 1 pause
