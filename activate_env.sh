#!/bin/bash
# Script to activate the virtual environment for this project

# Path to the virtual environment
VENV_PATH="$(pwd)/.venv"

if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_PATH"
    source "$VENV_PATH/bin/activate"
    echo "Python interpreter: $(which python3)"
    echo "Python version: $(python3 --version)"
    echo "Installed packages:"
    uv pip list
else
    echo "Virtual environment not found at $VENV_PATH"
    echo "Please run 'uv venv' to create a virtual environment"
fi
