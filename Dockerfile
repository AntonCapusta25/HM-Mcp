# Enhanced Dockerfile with full browser automation support
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HEADLESS=true
ENV USE_STEALTH=true
ENV DEBIAN_FRONTEND=noninteractive

# Install ALL browser dependencies (this is what's missing!)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    procps \
    # Browser automation dependencies
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    # Additional dependencies for interaction
    xvfb \
    libgconf-2-4 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    ca-certificates \
    fonts-liberation \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Verify browser and create symlink
RUN chromium --version && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome && \
    ln -sf /usr/bin/chromium /usr/bin/chrome

# Set browser environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-features=TranslateUI --disable-extensions --disable-component-extensions-with-background-pages --disable-default-apps --mute-audio --no-first-run --disable-background-networking"

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bulletproof_scraper.py .
COPY bulletproof_submitter.py .
COPY server.py .

# Create user with proper permissions for browser
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.config/chromium /home/appuser/.cache/chromium && \
    chown -R appuser:appuser /home/appuser/.config /home/appuser/.cache

USER appuser

# Create browser startup test
RUN echo '#!/bin/bash\necho "Testing browser..."\nchromium --headless --disable-gpu --no-sandbox --dump-dom about:blank > /dev/null 2>&1 && echo "✅ Browser works" || echo "❌ Browser failed"' > /home/appuser/test_browser.sh && \
    chmod +x /home/appuser/test_browser.sh

EXPOSE $PORT

# Enhanced health check that tests browser
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:$PORT/health && /home/appuser/test_browser.sh

CMD ["python", "server.py"]
