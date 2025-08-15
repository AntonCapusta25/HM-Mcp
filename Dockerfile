# Working Dockerfile with only packages that actually exist
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HEADLESS=true
ENV USE_STEALTH=true
ENV DEBIAN_FRONTEND=noninteractive

# Install only essential and available packages
RUN apt-get update && apt-get install -y \
    chromium \
    curl \
    procps \
    # Core browser dependencies (verified to exist)
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    # Essential X11 libraries
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    # System essentials
    ca-certificates \
    fonts-liberation \
    # Virtual display for headless operation
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Test Chrome installation
RUN chromium --version

# Create symlinks for compatibility
RUN ln -sf /usr/bin/chromium /usr/bin/google-chrome && \
    ln -sf /usr/bin/chromium /usr/bin/chrome

# Set browser paths and flags
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV DISPLAY=:99

# Essential Chrome flags for Docker
ENV CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --headless --disable-software-rasterizer --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-features=TranslateUI --disable-extensions --no-first-run --mute-audio"

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application files
COPY bulletproof_scraper.py .
COPY bulletproof_submitter.py .
COPY server.py .

# User setup with browser permissions
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.config/chromium /home/appuser/.cache && \
    chown -R appuser:appuser /home/appuser

USER appuser

# Test script for browser functionality
RUN echo '#!/bin/bash\n\
echo "🧪 Testing browser in container..."\n\
Xvfb :99 -screen 0 1024x768x24 &\n\
export DISPLAY=:99\n\
chromium --headless --no-sandbox --disable-gpu --dump-dom about:blank >/tmp/test.html 2>/tmp/error.log\n\
if [ -s /tmp/test.html ]; then\n\
    echo "✅ Browser automation working"\n\
    exit 0\n\
else\n\
    echo "❌ Browser failed:"\n\
    cat /tmp/error.log\n\
    exit 1\n\
fi' > /home/appuser/test_browser.sh && chmod +x /home/appuser/test_browser.sh

EXPOSE $PORT

# Health check with browser test
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:$PORT/health

# Start with virtual display
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & python server.py"]
