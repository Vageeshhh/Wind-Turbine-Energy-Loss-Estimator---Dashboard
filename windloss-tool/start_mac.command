#!/bin/bash
# Double-click to start the Outage Energy-Loss Estimator (macOS)
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python was not found. Install it from https://www.python.org/downloads/ and try again."
  read -p "Press Enter to close."
  exit 1
fi
if [ ! -d ".venv" ]; then
  echo "First start: setting up, this takes a few minutes..."
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
echo "Starting the app - your browser will open at http://localhost:8501"
echo "Close this window to stop the app."
python -m streamlit run app.py
