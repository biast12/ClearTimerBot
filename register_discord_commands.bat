@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM ClearTimerBot - Discord Command Synchronization Script
REM Purpose: Registers and synchronizes slash commands with Discord API
REM Usage: Run this after adding/modifying bot commands to update Discord
REM ============================================================================

REM Set console title for better identification
TITLE ClearTimerBot - Syncing Discord Commands

REM Check if Python is installed and accessible
python --version >nul 2>&1
IF %errorlevel% NEQ 0 (
    ECHO [ERROR] Python is not installed or not in PATH.
    ECHO Please install Python and ensure it's added to your system PATH.
    PAUSE
    EXIT /b 1
)

REM Check if register_discord_commands.py exists
IF NOT EXIST "register_discord_commands.py" (
    ECHO [ERROR] register_discord_commands.py not found in current directory.
    ECHO Please ensure the script exists before running this batch file.
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

REM Run the command synchronization script
python register_discord_commands.py

ECHO.
ECHO Press any key to exit...
PAUSE >nul