@echo off
cd /d "%~dp0"
echo Launching with python.exe (Console Visible)...
"C:\Users\darkp\AppData\Local\Microsoft\WindowsApps\python3.11.exe" "main.pyw"
echo Application exited with code %ERRORLEVEL%
pause
