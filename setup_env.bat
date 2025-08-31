@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM ClearTimerBot Environment Setup Script
REM This script creates a Python virtual environment and installs all required dependencies for the ClearTimerBot Discord bot.
REM ============================================================================

REM Set console title for better identification
TITLE ClearTimerBot - Environment Setup

REM Display script header
ECHO ============================================
ECHO     ClearTimerBot Environment Setup
ECHO ============================================
ECHO.

REM Check if Python is installed and accessible
python --version >nul 2>&1
IF %errorlevel% NEQ 0 (
    ECHO [ERROR] Python is not installed or not in PATH.
    ECHO Please install Python and ensure it's added to your system PATH.
    PAUSE
    EXIT /b 1
)

REM Check if virtual environment already exists
IF EXIST "venv\" (
    ECHO [INFO] Virtual environment already exists.
    CHOICE /C YN /M "Do you want to recreate it? (This will delete the existing environment)"
    IF !errorlevel! EQU 1 (
        ECHO [INFO] Removing existing virtual environment...
        RMDIR /S /Q venv
        ECHO [INFO] Existing environment removed.
        ECHO.
    ) ELSE (
        ECHO [INFO] Using existing virtual environment.
        GOTO :ACTIVATE_ENV
    )
)

REM Create new virtual environment
ECHO [INFO] Creating virtual environment...
python -m venv venv
IF %errorlevel% NEQ 0 (
    ECHO [ERROR] Failed to create virtual environment.
    PAUSE
    EXIT /b 1
)
ECHO [INFO] Virtual environment created successfully.
ECHO.

:ACTIVATE_ENV
REM Activate the virtual environment using Windows-specific activation script
ECHO [INFO] Activating virtual environment...
CALL venv\Scripts\activate.bat
IF %errorlevel% NEQ 0 (
    ECHO [ERROR] Failed to activate virtual environment.
    PAUSE
    EXIT /b 1
)
ECHO [INFO] Virtual environment activated.
ECHO.

REM Check if requirements.txt exists
IF NOT EXIST "requirements.txt" (
    ECHO [ERROR] requirements.txt not found in current directory.
    ECHO Please ensure requirements.txt exists before running this script.
    PAUSE
    EXIT /b 1
)

REM Upgrade pip to latest version before installing packages
ECHO [INFO] Upgrading pip to latest version...
python -m pip install --upgrade pip
ECHO.

REM Install required packages from requirements.txt
ECHO [INFO] Installing required packages...
pip install -r requirements.txt
IF %errorlevel% NEQ 0 (
    ECHO.
    ECHO [ERROR] Failed to install some packages.
    ECHO Please check the error messages above and requirements.txt file.
    PAUSE
    EXIT /b 1
)

REM Display success message
ECHO.
ECHO ============================================
ECHO [SUCCESS] Environment setup completed!
ECHO ============================================
ECHO.
ECHO Virtual environment is ready at: %CD%\venv
ECHO.
ECHO To activate the environment manually, run:
ECHO   venv\Scripts\activate.bat
ECHO.
ECHO To run the bot, use:
ECHO   run.bat
ECHO.
PAUSE