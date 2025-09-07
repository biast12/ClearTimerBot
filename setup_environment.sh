#!/bin/bash

# ============================================================================
# ClearTimerBot - Python Environment Setup
# Creates isolated Python environment and installs bot dependencies
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Display script header
echo "============================================"
echo "ClearTimerBot - Python Environment Setup"
echo "============================================"
echo

# Check if Python is installed and accessible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 is not installed or not in PATH.${NC}"
    echo "Please install Python3 and ensure it's added to your system PATH."
    exit 1
fi

# Check if virtual environment already exists
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}[INFO] Virtual environment already exists.${NC}"
    read -p "Do you want to recreate it? (This will delete the existing environment) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Removing existing virtual environment..."
        rm -rf venv
        echo "[INFO] Existing environment removed."
        echo
    else
        echo "[INFO] Using existing virtual environment."
        # Activate existing environment and skip to installation
        source venv/bin/activate
        echo
        # Jump to requirements installation
        if [ ! -f "requirements.txt" ]; then
            echo -e "${RED}[ERROR] requirements.txt not found in current directory.${NC}"
            echo "Please ensure requirements.txt exists before running this script."
            exit 1
        fi
        echo "[INFO] Upgrading pip to latest version..."
        python3 -m pip install --upgrade pip
        echo
        echo "[INFO] Installing required packages..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo
            echo -e "${RED}[ERROR] Failed to install some packages.${NC}"
            echo "Please check the error messages above and requirements.txt file."
            exit 1
        fi
        echo
        echo "============================================"
        echo -e "${GREEN}[SUCCESS] Environment setup completed!${NC}"
        echo "============================================"
        echo
        echo "Virtual environment is ready at: $(pwd)/venv"
        echo
        echo "To run the bot, use:"
        echo "  ./start_bot.sh"
        echo
        exit 0
    fi
fi

# Create new virtual environment
echo "[INFO] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to create virtual environment.${NC}"
    exit 1
fi
echo -e "${GREEN}[INFO] Virtual environment created successfully.${NC}"
echo

# Activate the virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment.${NC}"
    exit 1
fi
echo -e "${GREEN}[INFO] Virtual environment activated.${NC}"
echo

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}[ERROR] requirements.txt not found in current directory.${NC}"
    echo "Please ensure requirements.txt exists before running this script."
    exit 1
fi

# Upgrade pip to latest version before installing packages
echo "[INFO] Upgrading pip to latest version..."
python3 -m pip install --upgrade pip
echo

# Install required packages from requirements.txt
echo "[INFO] Installing required packages..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo
    echo -e "${RED}[ERROR] Failed to install some packages.${NC}"
    echo "Please check the error messages above and requirements.txt file."
    exit 1
fi

# Display success message
echo
echo "============================================"
echo -e "${GREEN}[SUCCESS] Environment setup completed!${NC}"
echo "============================================"
echo
echo "Virtual environment is ready at: $(pwd)/venv"
echo
echo "To run the bot, use:"
echo "  ./start_bot.sh"
echo