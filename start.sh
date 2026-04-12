#!/bin/bash

# FastMCP Skills Provider Server - Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.server.pid"
LOG_FILE="$SCRIPT_DIR/server.log"

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Error: FastMCP Skills Provider Server is already running (PID: $OLD_PID)"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# Create or clear log file
: > "$LOG_FILE"

# Check if Python environment is configured
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "Activating Python virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
elif command -v python3 &> /dev/null; then
    echo "Using system Python 3"
else
    echo "Error: Python 3 not found. Please install Python 3 or create a virtual environment."
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
fi

# Check if configuration file exists
if [ ! -f "$SCRIPT_DIR/skills.settings.json" ]; then
    echo "Configuration file not found. Creating default configuration..."
    python "$SCRIPT_DIR/main.py" --init
fi

# Start the server in background
echo "Starting FastMCP Skills Provider Server..."
nohup python "$SCRIPT_DIR/main.py" --config "$SCRIPT_DIR/skills.settings.json" > "$LOG_FILE" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

# Give the server a moment to start
sleep 1

# Check if server started successfully
if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "✓ FastMCP Skills Provider Server started successfully (PID: $SERVER_PID)"
    echo "  Log file: $LOG_FILE"
    echo "  PID file: $PID_FILE"
    echo ""
    echo "To view logs: tail -f $LOG_FILE"
    echo "To stop: ./stop.sh"
else
    echo "✗ Failed to start server. Check $LOG_FILE for details."
    cat "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
