@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM ClearTimerBot - Discord Command Registration
REM Registers and synchronizes slash commands with Discord API
REM ============================================================================

REM Set console title for better identification
TITLE ClearTimerBot - Discord Command Registration

REM Check if Python is installed and accessible
python --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Python is not installed or not in PATH.
    ECHO Please install Python and ensure it's added to your system PATH.
    PAUSE
    EXIT /B 1
)

REM Check if register_commands.py exists
IF NOT EXIST "register_commands.py" (
    ECHO [ERROR] register_commands.py not found in current directory.
    ECHO Please ensure the script exists before running this batch file.
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

REM Activate virtual environment and run the command synchronization
CALL venv\Scripts\activate.bat && python register_commands.py

ECHO.
ECHO Press any key to exit...
PAUSE >NUL