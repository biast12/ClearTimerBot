@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM ClearTimerBot - Main Bot Launcher
REM Purpose: Starts the ClearTimerBot Discord bot for automatic message clearing
REM Prerequisites: Python 3.8+ and configured .env file with bot token
REM ============================================================================

REM Set console title for better identification
TITLE ClearTimerBot - Active

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
    ECHO Please run setup_python_environment.bat first to set up the environment.
    PAUSE
    EXIT /b 1
)

REM Display bot startup message
ECHO [INFO] Launching ClearTimerBot...
ECHO ============================================
ECHO.
ECHO Bot Name: ClearTimerBot
ECHO Function: Automatic Message Clearing
ECHO Status:   INITIALIZING
ECHO.
ECHO Press Ctrl+C to gracefully shutdown the bot
ECHO.
ECHO ============================================
ECHO.

REM Run the main bot script
python main.py

REM Final pause before closing
ECHO.
ECHO Press any key to exit...
PAUSE >nul