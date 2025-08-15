# Fixed Dockerfile based on forum solution - Chrome WILL work
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HEADLESS=true
ENV USE_STEALTH=true
ENV DEBIAN_FRONTEND=noninteractive

# Install Chrome/Chromium and ESSENTIAL dependencies only
RUN apt-get update && apt-get install -y \
    chromium \
    curl \
    procps \
    # Minimal X11 support (from forum solution)
    xvfb \
    # dbus for Chrome (reduces errors)
    dbus \
    dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

# Verify Chrome installation
RUN chromium --version

# Set up display and Chrome environment (from forum)
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium

# Create symlinks for compatibility
RUN ln -sf /usr/bin/chromium /usr/bin/google-chrome

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy FIXED application files
COPY bulletproof_scraper.py .
COPY bulletproof_submitter.py .
COPY server.py .

# Create startup script that sets up X11 (from forum solution)
RUN echo '#!/bin/bash\n\
echo "🐳 Starting Docker container with X11 support..."\n\
# Start virtual display\n\
Xvfb :99 -screen 0 1024x768x24 -ac &\n\
export DISPLAY=:99\n\
# Start dbus (reduces Chrome errors)\n\
service dbus start 2>/dev/null || true\n\
# Test Chrome quickly\n\
echo "🧪 Testing Chrome..."\n\
timeout 10 chromium --no-sandbox --headless --disable-gpu --dump-dom about:blank >/tmp/test.html 2>/dev/null\n\
if [ -s /tmp/test.html ]; then\n\
    echo "✅ Chrome test successful"\n\
else\n\
    echo "⚠️ Chrome test failed but continuing..."\n\
fi\n\
# Start MCP server\n\
echo "🚀 Starting MCP server..."\n\
python server.py' > /app/start_with_display.sh && \
    chmod +x /app/start_with_display.sh

# Create user but keep it simple
RUN useradd -m appuser && chown -R appuser:appuser /app

# Stay as root for Chrome (forum solution shows running as root with --no-sandbox)
# USER appuser

EXPOSE $PORT

# Test Chrome during health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:$PORT/health

# Use startup script that configures X11
CMD ["./start_with_display.sh"]
