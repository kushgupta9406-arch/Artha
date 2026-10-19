@echo off
title ARTHA
cd /d "%~dp0"
set PYTHONUTF8=1
if exist ".venv\Scripts\python.exe" goto run

echo ============================================
echo  ARTHA first-time setup (about 3-5 minutes)
echo ============================================
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Python was not found. Installing Python 3.12...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)
%PY% -m venv .venv
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo Could not set up Python. Install Python 3.12 from https://www.python.org/downloads/
  echo ^(tick "Add python.exe to PATH"^), then double-click this file again.
  pause
  exit /b 1
)
echo Installing ARTHA's packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

:run
echo.
echo Starting ARTHA... your browser will open at http://localhost:8501
echo Keep this window open while you use ARTHA. Close it to stop the app.
start "" cmd /c "timeout /t 6 >nul & start http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --server.port 8501
pause
