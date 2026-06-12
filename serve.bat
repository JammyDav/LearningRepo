@echo off
echo Serving http://localhost:8000  (Ctrl+C to stop)
cd /d "%~dp0web"
python -m http.server 8000
