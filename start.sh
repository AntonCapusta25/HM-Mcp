#!/bin/bash

# Form Automation MCP Server Startup Script for Docker
# Handles environment setup and graceful startup

set -e  # Exit on any error

echo "🐳 Starting Form Automation MCP Server in Docker..."
echo "📅 $(date)"
echo ""

# Environment info
echo "🔧 Environment Configuration:"
echo "  - Port: ${PORT:-8000}"
echo "  - Headless: ${HEADLESS:-true}"
echo "  - Stealth: ${USE_STEALTH:-true}"
echo "  - Debug: ${DEBUG:-false}"
echo ""

# Check Chrome installation
echo "🌐 Browser Check:"
if command -v google-chrome &> /dev/null; then
    echo "  ✅ Google Chrome found"
    CHROME_VERSION=$(google-chrome --version 2>/dev/null || echo "Unknown")
    echo "  📝 Version: $CHROME_VERSION"
elif command -v chromium &> /dev/null; then
    echo "  ✅ Chromium found"
    CHROME_VERSION=$(chromium --version 2>/dev/null || echo "Unknown")
    echo "  📝 Version: $CHROME_VERSION"
else
    echo "  ⚠️  No Chrome/Chromium found - this may cause issues"
fi
echo ""

# Check Python modules
echo "🐍 Python Module Check:"
python3 -c "
import sys
modules = ['fastmcp', 'pydantic', 'DrissionPage', 'requests']
for module in modules:
    try:
        __import__(module)
        print(f'  ✅ {module}')
    except ImportError:
        print(f'  ❌ {module} - MISSING')
        sys.exit(1)
"
echo ""

# Check required files
echo "📁 File Check:"
for file in "server.py" "bulletproof_scraper.py" "bulletproof_submitter.py"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING"
        exit 1
    fi
done
echo ""

# Set default environment variables if not set
export PORT=${PORT:-8000}
export HEADLESS=${HEADLESS:-true}
export USE_STEALTH=${USE_STEALTH:-true}
export DEBUG=${DEBUG:-false}

# Chrome flags for Docker environment
export CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer"

echo "🚀 Starting MCP Server..."
echo "🔗 Server will be available at: http://0.0.0.0:$PORT"
echo ""

# Handle shutdown gracefully
trap 'echo "🛑 Shutting down server..."; kill $SERVER_PID 2>/dev/null; exit 0' SIGTERM SIGINT

# Start the server in background and capture PID
python3 server.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server is actually running
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ Server started successfully (PID: $SERVER_PID)"
    echo "🏥 Health check endpoint: http://0.0.0.0:$PORT/health"
    echo ""
    echo "📊 Server is ready to accept connections!"
    
    # Wait for the server process
    wait $SERVER_PID
else
    echo "❌ Server failed to start"
    exit 1
fi
