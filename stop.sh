#!/bin/bash

# FastMCP Skills Provider Server - Stop Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.server.pid"

SERVER_PID=""

if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        rm -f "$PID_FILE"
        unset SERVER_PID
    fi
fi

if [ -z "$SERVER_PID" ]; then
    for pid in $(pgrep -f "python.*main.*py" 2>/dev/null); do
        if [ -d "/proc/$pid/cwd" ]; then
            if readlink "/proc/$pid/cwd" 2>/dev/null | grep -q "skillsmcp"; then
                SERVER_PID="$pid"
                break
            fi
        fi
    done
fi

if [ -z "$SERVER_PID" ]; then
    echo "Error: Server is not running"
    echo ""
    echo "Note: If the server is running via stdio transport (started by Claude Code"
    echo "or another MCP client), it cannot be stopped with this script."
    echo "Stop the parent MCP client to stop the server."
    exit 1
fi

if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Error: Server process (PID: $SERVER_PID) is not running"
    rm -f "$PID_FILE"
    exit 1
fi

echo "Stopping FastMCP Skills Provider Server (PID: $SERVER_PID)..."
kill -TERM "$SERVER_PID" 2>/dev/null || true

for i in {1..10}; do
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        break
    fi
    sleep 0.5
done

if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Forcing shutdown..."
    kill -9 "$SERVER_PID" 2>/dev/null || true
    sleep 1
fi

rm -f "$PID_FILE"

if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "✓ FastMCP Skills Provider Server stopped successfully"
else
    echo "✗ Failed to stop server. PID: $SERVER_PID"
    exit 1
fi