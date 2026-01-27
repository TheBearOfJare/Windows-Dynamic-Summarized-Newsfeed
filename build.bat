@echo off
echo Building GeminiNewsfeed...
python -m PyInstaller --noconsole --onefile --add-data "icon.png;." --icon=icon.png --name="GeminiNewsfeed" main.pyw
echo Build complete. The executable is in the "dist" folder.
pause
