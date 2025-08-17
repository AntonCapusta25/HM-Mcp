#!/bin/bash

# Email MCP Server Start Script
# Professional email automation for Claude

echo "📧 Starting Email MCP Server..."
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if required files exist
required_files=("email_server.py" "bulletproof_emailer.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

# Check if email credentials are configured
if [ -z "$EMAIL_USER" ] || [ -z "$EMAIL_PASSWORD" ]; then
    echo "⚠️  Email credentials not configured!"
    echo ""
    echo "Set up your email credentials:"
    echo "export EMAIL_USER='your_email@gmail.com'"
    echo "export EMAIL_PASSWORD='your_app_password'"
    echo ""
    echo "For Gmail:"
    echo "1. Enable 2-factor authentication"
    echo "2. Generate an app password"
    echo "3. Use the app password (not your regular password)"
    echo ""
    read -p "Continue anyway? (y/N): " continue_choice
    if [[ ! $continue_choice =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set default environment variables if not set
export SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}"
export SMTP_PORT="${SMTP_PORT:-587}"
export USE_TLS="${USE_TLS:-true}"
export PORT="${PORT:-8001}"
export DEBUG="${DEBUG:-false}"

echo "📋 Configuration:"
echo "  • SMTP Server: $SMTP_SERVER:$SMTP_PORT"
echo "  • Email User: ${EMAIL_USER:-Not configured}"
echo "  • TLS Enabled: $USE_TLS"
echo "  • Server Port: $PORT"
echo "  • Debug Mode: $DEBUG"
echo ""

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Email MCP Server..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the server
echo "🚀 Starting Email MCP Server on port $PORT..."
echo "💡 Use Ctrl+C to stop the server"
echo ""

# Run the email server
python3 email_server.py

# If we get here, the server stopped
echo "📧 Email MCP Server stopped."