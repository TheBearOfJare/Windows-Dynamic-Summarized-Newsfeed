@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Building EXE...
pyinstaller GeminiNewsfeed.spec --clean --noconfirm

echo Copying external resources...
copy interests.txt dist\
copy README.md dist\


echo Build complete.
pause
