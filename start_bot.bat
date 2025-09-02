@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

REM =====================================================
REM ClearTimerBot - Bot Launcher
REM =====================================================

REM Set console title for better identification
TITLE ClearTimerBot - Bot Launcher

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

REM Parse command line arguments
SET SHARD_COUNT=
SET SHARD_IDS=

:PARSE_ARGS
IF "%~1"=="" GOTO RUN_BOT
IF /I "%~1"=="--shards" (
    SET SHARD_COUNT=%~2
    SHIFT
    SHIFT
    GOTO PARSE_ARGS
)
IF /I "%~1"=="--shard-ids" (
    SET SHARD_IDS=%~2
    SHIFT
    SHIFT
    GOTO PARSE_ARGS
)
SHIFT
GOTO PARSE_ARGS

:RUN_BOT

REM Build the command
SET CMD=python shard_launcher.py

IF DEFINED SHARD_COUNT (
    SET CMD=%CMD% --shards %SHARD_COUNT%
    ECHO Configured shards: %SHARD_COUNT%
)

IF DEFINED SHARD_IDS (
    SET CMD=%CMD% --shard-ids "%SHARD_IDS%"
    ECHO Running shard IDs: %SHARD_IDS%
)

IF NOT DEFINED SHARD_COUNT IF NOT DEFINED SHARD_IDS (
    ECHO Auto-detecting optimal shard count...
)

ECHO.
ECHO Launching bot...
ECHO =====================================================
ECHO.

REM Activate virtual environment and run the sharding launcher
CALL venv\Scripts\activate.bat && %CMD%

REM Check if bot crashed
if %ERRORLEVEL% neq 0 (
    ECHO.
    ECHO =====================================================
    ECHO [ERROR] Bot crashed with error code: %ERRORLEVEL%
    ECHO =====================================================
    PAUSE
) else (
    ECHO.
    ECHO =====================================================
    ECHO Bot stopped normally.
    ECHO =====================================================
)

REM Deactivate virtual environment
deactivate

PAUSE