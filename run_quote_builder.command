#!/bin/bash
# TBG Quote Builder Launcher
# Double-click this file to run the Quote Builder

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment and run
source tbg_env/bin/activate
python tbg_quote_builder.py
