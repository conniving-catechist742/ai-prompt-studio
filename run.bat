@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :error
start "" ".venv\Scripts\pythonw.exe" app.py
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5000
exit /b 0

:error
echo PromptForge could not start. Check that Python 3 is installed and try again.
pause
exit /b 1
