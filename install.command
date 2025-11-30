#!/bin/bash
# TBG Quote Builder - Mac Installation Script
# This script sets up everything needed to run the Quote Builder

echo "============================================"
echo "  TBG Enterprises Quote Builder Installer"
echo "============================================"
echo ""

# Check if Python 3 is installed
if command -v python3 &> /dev/null; then
    echo "✓ Python 3 found"
    PYTHON_CMD="python3"
else
    echo "✗ Python 3 not found"
    echo ""
    echo "Please install Python 3 first:"
    echo "1. Go to https://www.python.org/downloads/"
    echo "2. Download Python 3.11 or later for macOS"
    echo "3. Run the installer"
    echo "4. Re-run this setup script"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv tbg_env

if [ $? -ne 0 ]; then
    echo "✗ Failed to create virtual environment"
    echo "  Try: $PYTHON_CMD -m pip install --upgrade pip virtualenv"
    exit 1
fi
echo "✓ Virtual environment created"

# Activate virtual environment
source tbg_env/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install required packages
echo ""
echo "Installing required packages..."
pip install reportlab pillow pymupdf > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "✗ Failed to install packages"
    exit 1
fi
echo "✓ reportlab installed"
echo "✓ pillow installed (for images)"
echo "✓ pymupdf installed (for PDF attachments)"

# Make the launcher script executable
chmod +x run_quote_builder.command

echo ""
echo "============================================"
echo "  Installation Complete!"
echo "============================================"
echo ""
echo "To run the Quote Builder:"
echo "  • Double-click 'run_quote_builder.command'"
echo ""
echo "Or from Terminal:"
echo "  cd $(pwd)"
echo "  source tbg_env/bin/activate"
echo "  python tbg_quote_builder.py"
echo ""
