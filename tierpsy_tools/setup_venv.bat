
@echo off
setlocal

REM Exit if a command fails
set "ENV_DIR=.venv"
set "REQ_FILE=requirements.txt"

REM 1. Check if requirements.txt exists
if not exist "%REQ_FILE%" (
    echo Error: %REQ_FILE% not found in the current directory.
    exit /b 1
)

REM 2. Create the virtual environment
echo Creating virtual environment in "%ENV_DIR%"...
python -m venv "%ENV_DIR%"
if errorlevel 1 exit /b 1

REM 3. Activate the environment
echo Activating virtual environment...
call "%ENV_DIR%\Scripts\activate.bat"
if errorlevel 1 exit /b 1

REM 4. Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

REM 5. Install requirements
echo Installing packages from %REQ_FILE%...
python -m pip install -r "%REQ_FILE%"
if errorlevel 1 exit /b 1

echo.
echo Setup complete!
echo To activate the environment manually, run:
echo call %ENV_DIR%\Scripts\activate.bat

endlocal
