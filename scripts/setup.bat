@echo off
setlocal
cd /d "%~dp0.."
set PY=python
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Python 3.10-3.12 not found. Install it from python.org and tick "Add Python to PATH".
    exit /b 1
  )
  set PY=py -3
)
if not exist .venv (
  echo Creating virtual environment .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo ERROR: could not create the virtual environment.
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: installing requirements failed. Check your internet connection and Python version.
  exit /b 1
)
if not exist .env copy .env.example .env >nul
echo.
echo Setup complete. Put the private CSV files in the data folder, then run scripts\run_local.bat
