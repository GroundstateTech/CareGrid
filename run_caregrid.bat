@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating CareGrid virtual environment...
  py -3 -m venv .venv 2>nul || python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul
if not exist ".venv\.caregrid_deps_ready" (
  echo Installing CareGrid dependencies...
  pip install -r requirements.txt
  if errorlevel 1 goto :error
  type nul > ".venv\.caregrid_deps_ready"
)
python caregrid_app.py
if errorlevel 1 goto :error
goto :eof
:error
echo.
echo CareGrid exited with an error. Review the message above.
pause
endlocal
