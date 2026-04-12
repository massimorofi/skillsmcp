#!/bin/bash

# FastMCP Skills Provider Server - Setup Script
# This script sets up the development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "FastMCP Skills Provider Server - Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install -q --upgrade pip
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Dependencies installed"
echo ""

# Create configuration file if needed
if [ ! -f "$SCRIPT_DIR/skills.settings.json" ]; then
    echo "Creating default configuration file..."
    python "$SCRIPT_DIR/main.py" --init
    echo "✓ Configuration file created"
else
    echo "✓ Configuration file already exists"
fi
echo ""

# Create skills directories from config if they don't exist
echo "Ensuring skill directories exist..."
mkdir -p "$SCRIPT_DIR/skills"
echo "✓ Local skills directory ready"
echo ""

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and edit skills.settings.json as needed"
echo "2. Add skills to configured directories"
echo "3. Run ./start.sh to start the server"
echo ""
echo "Commands:"
echo "  ./start.sh        - Start the server"
echo "  ./stop.sh         - Stop the server"
echo "  tail -f server.log - View server logs"
echo ""
