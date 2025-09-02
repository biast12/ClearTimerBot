@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM ClearTimerBot - Development Bot Launcher
REM ============================================================================

REM Set console title for better identification
TITLE ClearTimerBot - Development Bot Launcher

REM Check if Python is installed and accessible
python --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Python is not installed or not in PATH.
    ECHO Please install Python and ensure it's added to your system PATH.
    PAUSE
    EXIT /B 1
)

REM Check if virtual environment exists and offer to activate it
IF NOT EXIST "venv\Scripts\activate.bat" (
    ECHO [WARNING] No virtual environment found.
    ECHO Please run setup_environment.bat first to set up the environment.
    PAUSE
    EXIT /B 1
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

REM Activate virtual environment and run the main bot script
CALL venv\Scripts\activate.bat && python main.py

ECHO.
ECHO Press any key to exit...
PAUSE >NUL