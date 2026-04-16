@echo off
REM Setup script for Media Influence Analysis Project (Windows)

echo ==================================
echo Setting up Media Influence Project
echo ==================================

REM Check Python
echo.
echo Checking Python version...
python --version
if errorlevel 1 (
    echo Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file
echo.
if exist .env (
    echo .env file already exists. Skipping...
) else (
    echo Creating .env file from template...
    copy .env.template .env
    echo .env file created. Please edit it with your Telegram API credentials.
)

REM Create data directories
echo.
echo Creating data directories...
mkdir data\raw 2>nul
mkdir data\processed 2>nul
mkdir data\results 2>nul

echo.
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo Next steps:
echo 1. Edit .env file with your Telegram API credentials
echo 2. Get credentials from: https://my.telegram.org/apps
echo 3. Run: python main.py all
echo.
echo For detailed instructions, see QUICKSTART.md
echo.
pause
