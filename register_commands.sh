#!/bin/bash

# ============================================================================
# ClearTimerBot - Discord Command Registration
# Registers and synchronizes slash commands with Discord API
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Display script header
echo "============================================"
echo "ClearTimerBot - Discord Command Registration"
echo "============================================"
echo

# Check if Python is installed and accessible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 is not installed or not in PATH.${NC}"
    echo "Please install Python3 and ensure it's added to your system PATH."
    exit 1
fi

# Check if register_commands.py exists
if [ ! -f "register_commands.py" ]; then
    echo -e "${RED}[ERROR] register_commands.py not found in current directory.${NC}"
    echo "Please ensure the script exists before running this script."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}[WARNING] No virtual environment found.${NC}"
    echo "Please run ./setup_environment.sh first to set up the environment."
    exit 1
fi

# Activate virtual environment and run the command synchronization
source venv/bin/activate && python3 register_commands.py

echo
echo "Press Enter to exit..."
read