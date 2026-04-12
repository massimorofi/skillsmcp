#!/bin/bash

# FastMCP Skills Provider Server - Stop Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.server.pid"

# Check if server is running
if [ ! -f "$PID_FILE" ]; then
    echo "Error: Server is not running (PID file not found)"
    exit 1
fi

SERVER_PID=$(cat "$PID_FILE")

# Check if process exists
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Error: Server process (PID: $SERVER_PID) is not running"
    rm -f "$PID_FILE"
    exit 1
fi

# Try graceful shutdown first
echo "Stopping FastMCP Skills Provider Server (PID: $SERVER_PID)..."
kill -TERM "$SERVER_PID" 2>/dev/null || true

# Wait for graceful shutdown
for i in {1..10}; do
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        break
    fi
    sleep 0.5
done

# Force kill if necessary
if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Forcing shutdown..."
    kill -9 "$SERVER_PID" 2>/dev/null || true
    sleep 1
fi

# Clean up
rm -f "$PID_FILE"

if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "✓ FastMCP Skills Provider Server stopped successfully"
else
    echo "✗ Failed to stop server. PID: $SERVER_PID"
    exit 1
fi
