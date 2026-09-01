@echo off
setlocal
set "KUMONOS_DIR=%~dp0"
set "PYTHONPATH=%KUMONOS_DIR%src"
set "LOG_DIR=%KUMONOS_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "PYTHON_EXE=C:\Users\l-munehiko.a.nagase\AppData\Local\Programs\Python\Python312\python.exe"

echo ---- %date% %time% ---- >> "%LOG_DIR%\compile.log"
cd /d "%KUMONOS_DIR%"
"%PYTHON_EXE%" -m kumonos.cli compile --config kumonos.json >> "%LOG_DIR%\compile.log" 2>&1
echo exit code %errorlevel% >> "%LOG_DIR%\compile.log"
endlocal
