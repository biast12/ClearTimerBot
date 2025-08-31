@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM ClearTimerBot Discord Command Registration Script
REM This script registers or updates slash commands with Discord for the ClearTimerBot.
REM ============================================================================

REM Set console title for better identification
TITLE ClearTimerBot - Command Registration

REM Check if Python is installed and accessible
python --version >nul 2>&1
IF %errorlevel% NEQ 0 (
    ECHO [ERROR] Python is not installed or not in PATH.
    ECHO Please install Python and ensure it's added to your system PATH.
    PAUSE
    EXIT /b 1
)

REM Check if register_commands.py exists
IF NOT EXIST "register_commands.py" (
    ECHO [ERROR] register_commands.py not found in current directory.
    ECHO Please ensure the script exists before running this batch file.
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

REM Run the command registration script
ECHO [INFO] Starting command registration...
ECHO ============================================
ECHO.
python register_commands.py

ECHO.
ECHO Press any key to exit...
PAUSE >nul