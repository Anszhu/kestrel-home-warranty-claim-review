@echo off
cd /d "%~dp0.."
echo Starting the API (port 8000) and Streamlit in two windows...
start "Kestrel API" cmd /k scripts\run_api.bat
timeout /t 4 /nobreak >nul
start "Kestrel Streamlit" cmd /k scripts\run_streamlit.bat
echo Streamlit: http://localhost:8501   API docs: http://127.0.0.1:8000/docs
