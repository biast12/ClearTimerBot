#!/bin/bash

# =====================================================
# ClearTimerBot - Bot Launcher
# =====================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display script header
echo "============================================"
echo "ClearTimerBot - Bot Launcher"
echo "============================================"
echo

# Check if Python is installed and accessible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 is not installed or not in PATH.${NC}"
    echo "Please install Python3 and ensure it's added to your system PATH."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}[WARNING] No virtual environment found.${NC}"
    echo "Please run ./setup_environment.sh first to set up the environment."
    exit 1
fi

# Parse command line arguments
SHARD_COUNT=""
SHARD_IDS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --shards)
            SHARD_COUNT="$2"
            shift 2
            ;;
        --shard-ids)
            SHARD_IDS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Build the command
CMD="python3 main.py"

if [ -n "$SHARD_COUNT" ]; then
    CMD="$CMD --shards $SHARD_COUNT"
    echo -e "${BLUE}Configured shards: $SHARD_COUNT${NC}"
fi

if [ -n "$SHARD_IDS" ]; then
    CMD="$CMD --shard-ids \"$SHARD_IDS\""
    echo -e "${BLUE}Running shard IDs: $SHARD_IDS${NC}"
fi

if [ -z "$SHARD_COUNT" ] && [ -z "$SHARD_IDS" ]; then
    echo -e "${BLUE}Auto-detecting optimal shard count...${NC}"
fi

echo
echo "Launching bot..."
echo "============================================="
echo

# Activate virtual environment and run the main bot
source venv/bin/activate && eval $CMD
EXIT_CODE=$?

# Check if bot crashed
if [ $EXIT_CODE -ne 0 ]; then
    echo
    echo "============================================="
    echo -e "${RED}[ERROR] Bot crashed with error code: $EXIT_CODE${NC}"
    echo "============================================="
else
    echo
    echo "============================================="
    echo -e "${GREEN}Bot stopped normally.${NC}"
    echo "============================================="
fi

# Deactivate virtual environment
deactivate 2>/dev/null

echo
echo "Press Enter to exit..."
read