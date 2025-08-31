@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM ClearTimerBot Main Execution Script
REM This script starts the ClearTimerBot Discord bot.
REM ============================================================================

REM Set console title for better identification
TITLE ClearTimerBot - Running

REM Check if Python is installed and accessible
python --version >nul 2>&1
IF %errorlevel% NEQ 0 (
    ECHO [ERROR] Python is not installed or not in PATH.
    ECHO Please install Python and ensure it's added to your system PATH.
    PAUSE
    EXIT /b 1
)

REM Check if virtual environment exists and offer to activate it
IF NOT EXIST "venv\Scripts\activate.bat" (
    ECHO [WARNING] No virtual environment found.
    ECHO Please run setup_env.bat first to set up the environment.
    PAUSE
    EXIT /b 1
)

REM Display bot startup message
ECHO [INFO] Starting ClearTimerBot...
ECHO ============================================
ECHO.
ECHO Bot Status: STARTING
ECHO Press Ctrl+C to stop the bot
ECHO.
ECHO ============================================
ECHO.

REM Run the main bot script
python main.py

REM Final pause before closing
ECHO.
ECHO Press any key to exit...
PAUSE >nul