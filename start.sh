#!/bin/bash

# Enhanced Form Automation Server Startup Script
set -e

echo "🚀 Starting Enhanced Form Automation Server..."

# Set up virtual display for headless mode
if [ "$HEADLESS" = "true" ]; then
    echo "🖥️  Setting up virtual display..."
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    XVFB_PID=$!
    echo "✅ Virtual display started (PID: $XVFB_PID)"
    
    # Wait for display to be ready
    sleep 2
fi

# Verify Chrome installation
if command -v google-chrome-stable &> /dev/null; then
    echo "✅ Chrome found: $(google-chrome-stable --version)"
    export CHROME_BIN=$(which google-chrome-stable)
elif command -v google-chrome &> /dev/null; then
    echo "✅ Chrome found: $(google-chrome --version)"
    export CHROME_BIN=$(which google-chrome)
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium found: $(chromium-browser --version)"
    export CHROME_BIN=$(which chromium-browser)
else
    echo "⚠️  Warning: No Chrome/Chromium found, enhanced features may not work"
fi

# Test Chrome functionality
if [ -n "$CHROME_BIN" ]; then
    echo "🧪 Testing Chrome functionality..."
    timeout 10s $CHROME_BIN --headless --disable-gpu --no-sandbox --version > /dev/null 2>&1 && \
    echo "✅ Chrome test successful" || \
    echo "⚠️  Chrome test failed"
fi

# Set Chrome flags for container environment
export CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-web-security --disable-features=site-per-process --no-first-run --no-service-autorun --disable-default-apps"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down..."
    if [ -n "$XVFB_PID" ]; then
        kill $XVFB_PID 2>/dev/null || true
        echo "✅ Virtual display stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

echo "🎯 Starting Python application..."
echo "📊 Configuration:"
echo "   - Headless: $HEADLESS"
echo "   - Stealth: $USE_STEALTH" 
echo "   - Port: ${PORT:-8083}"
echo "   - Chrome: $CHROME_BIN"

# Start the main application
python main.py &
APP_PID=$!

echo "✅ Application started (PID: $APP_PID)"
echo "🌐 Server should be available on port ${PORT:-8083}"

# Wait for the application
wait $APP_PID

# Cleanup on exit
cleanup
