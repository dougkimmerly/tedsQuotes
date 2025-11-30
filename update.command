#!/bin/bash
# TBG Quote Builder - Update Script
# Double-click this to check for and install updates

echo "============================================"
echo "  TBG Quote Builder - Checking for Updates"
echo "============================================"
echo ""

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Xcode Command Line Tools:"
    echo "  xcode-select --install"
    exit 1
fi

# Check if this is a git repo
if [ ! -d ".git" ]; then
    echo "This folder is not connected to GitHub."
    echo "Updates must be downloaded manually."
    exit 1
fi

# Fetch updates
echo "Checking GitHub for updates..."
git fetch origin main

# Check if there are updates
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo ""
    echo "✓ You're already running the latest version!"
    echo ""
else
    echo ""
    echo "Updates available! Downloading..."
    echo ""
    
    # Pull updates
    git pull origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Update complete!"
        echo ""
        echo "Updating packages..."
        source tbg_env/bin/activate
        pip install --upgrade reportlab pillow pymupdf > /dev/null 2>&1
        echo "✓ Packages updated!"
        echo ""
        echo "============================================"
        echo "  Update successful! You can now run the"
        echo "  Quote Builder with the latest features."
        echo "============================================"
    else
        echo ""
        echo "✗ Update failed. Please try again or contact support."
    fi
fi

echo ""
echo "Press Enter to close..."
read
