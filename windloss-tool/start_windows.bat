@echo off
REM Double-click to start the Outage Energy-Loss Estimator (Windows)
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during installation.
  pause
  exit /b 1
)
if not exist ".venv" (
  echo First start: setting up, this takes a few minutes...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
echo Starting the app - your browser will open at http://localhost:8501
echo Close this window to stop the app.
python -m streamlit run app.py
pause
