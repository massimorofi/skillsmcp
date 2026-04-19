#!/bin/bash

# FastMCP Skills Provider Server - Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.server.pid"
LOG_FILE="$SCRIPT_DIR/server.log"
HTTP_LOG_FILE="$SCRIPT_DIR/server-http.log"
HTTP_PID_FILE="$SCRIPT_DIR/.server-http.pid"

TRANSPORT="${1:-stdio}"
HTTP_PORT="${2:-3001}"

check_virt_env() {
    if [ -d "$SCRIPT_DIR/venv" ]; then
        source "$SCRIPT_DIR/venv/bin/activate"
    fi
}

get_http_port() {
    python3 -c "
import json
with open('$SCRIPT_DIR/skills.settings.json') as f:
    d = json.load(f)
print(d.get('http', {}).get('port', 3001))
" 2>/dev/null || echo "3001"
}

get_gateway_host() {
    python3 -c "
import json
with open('$SCRIPT_DIR/skills.settings.json') as f:
    d = json.load(f)
print(d.get('gateway', {}).get('host', 'localhost'))
" 2>/dev/null || echo "localhost"
}

get_gateway_port() {
    python3 -c "
import json
with open('$SCRIPT_DIR/skills.settings.json') as f:
    d = json.load(f)
print(d.get('gateway', {}).get('port', 8000))
" 2>/dev/null || echo "8000"
}

get_gateway_name() {
    python3 -c "
import json
with open('$SCRIPT_DIR/skills.settings.json') as f:
    d = json.load(f)
print(d.get('gateway', {}).get('name', 'skills-provider'))
" 2>/dev/null || echo "skills-provider"
}

register_to_gateway() {
    local server_url="http://localhost:$HTTP_PORT/mcp"
    local gw_host="$1"
    local gw_port="$2"
    local server_name="$3"
    
    echo "Registering to MCP Gateway at http://$gw_host:$gw_port..."
    
    # Unregister first if already registered
    curl -s -X DELETE "http://$gw_host:$gw_port/registry/servers" \
        -H "Content-Type: application/json" \
        -d "{\"id\":\"$server_name\"}" > /dev/null 2>&1
    
    local response=$(curl -s -X POST "http://$gw_host:$gw_port/registry/servers" \
        -H "Content-Type: application/json" \
        -d "{\"id\":\"$server_name\",\"transport\":\"sse\",\"url\":\"$server_url\"}" 2>&1)
    
    if echo "$response" | grep -q "error\|detail"; then
        echo "✗ Failed to register: $response"
        return 1
    else
        echo "✓ Registered to MCP Gateway"
        return 0
    fi
}

print_register_cmd() {
    local GW_HOST="$1"
    local GW_PORT="$2"
    local GW_NAME="$3"
    local HTTP_PORT="$4"
    
    echo ""
    echo "To register with MCP Gateway:"
    echo "  curl -X POST http://$GW_HOST:$GW_PORT/registry/servers \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"id\":\"$GW_NAME\",\"transport\":\"sse\",\"url\":\"http://localhost:$HTTP_PORT/mcp\"}'"
}

start_stdio() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "Error: FastMCP Skills Provider Server is already running (PID: $OLD_PID)"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    : > "$LOG_FILE"
    check_virt_env

    echo "Starting FastMCP Skills Provider Server (stdio transport)..."
    nohup python "$SCRIPT_DIR/main.py" --config "$SCRIPT_DIR/skills.settings.json" > "$LOG_FILE" 2>&1 &

    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"

    sleep 1

    if kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "✓ FastMCP Skills Provider Server started (PID: $SERVER_PID)"
        echo "  Log: $LOG_FILE"
    else
        echo "✗ Failed to start server. Check $LOG_FILE"
        cat "$LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

start_http() {
    if [ -f "$HTTP_PID_FILE" ]; then
        OLD_PID=$(cat "$HTTP_PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "Error: HTTP server already running (PID: $OLD_PID)"
            exit 1
        else
            rm -f "$HTTP_PID_FILE"
        fi
    fi

    HTTP_PORT=$(get_http_port)
    GW_HOST=$(get_gateway_host)
    GW_PORT=$(get_gateway_port)
    GW_NAME=$(get_gateway_name)

    : > "$HTTP_LOG_FILE"
    check_virt_env

    echo "Starting FastMCP Skills Provider Server (HTTP transport)..."
    echo "  Port: $HTTP_PORT"
    nohup python "$SCRIPT_DIR/main.py" --http --port "$HTTP_PORT" > "$HTTP_LOG_FILE" 2>&1 &

    SERVER_PID=$!
    echo $SERVER_PID > "$HTTP_PID_FILE"

    sleep 2

    if kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "✓ FastMCP Skills Provider HTTP server started (PID: $SERVER_PID)"
        echo "  URL: http://localhost:$HTTP_PORT/mcp"
        echo "  Log: $HTTP_LOG_FILE"
        
        # Auto-register to gateway if enabled
        if grep -q '"enabled".*true' "$SCRIPT_DIR/skills.settings.json" && grep -A2 '"gateway"' "$SCRIPT_DIR/skills.settings.json" | grep -q '"enabled".*true'; then
            register_to_gateway "$GW_HOST" "$GW_PORT" "$GW_NAME"
        else
            print_register_cmd "$GW_HOST" "$GW_PORT" "$GW_NAME" "$HTTP_PORT"
        fi
    else
        echo "✗ Failed to start HTTP server. Check $HTTP_LOG_FILE"
        cat "$HTTP_LOG_FILE"
        rm -f "$HTTP_PID_FILE"
        exit 1
    fi
}

check_http_enabled() {
    if [ -f "$SCRIPT_DIR/skills.settings.json" ]; then
        if grep -A2 '"http"' "$SCRIPT_DIR/skills.settings.json" | grep -q '"enabled".*true'; then
            return 0
        fi
    fi
    return 1
}

TRANSPORT_MODE="$1"

if [ -z "$TRANSPORT_MODE" ] && check_http_enabled; then
    TRANSPORT_MODE="http"
fi

if [ -z "$TRANSPORT_MODE" ]; then
    TRANSPORT_MODE="stdio"
fi

case "$TRANSPORT_MODE" in
    http|https)
        start_http
        ;;
    stdio)
        start_stdio
        ;;
    *)
        echo "Usage: $0 [stdio|http] [port]"
        echo ""
        echo "Examples:"
        echo "  $0           # Start with stdio transport (or http if enabled in config)"
        echo "  $0 http      # Start with HTTP transport"
        echo "  $0 http 3001 # Start with HTTP on port 3001"
        exit 1
        ;;
esac