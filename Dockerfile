# Ultra-Reliable Dockerfile using system Chromium (no repository issues)
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HEADLESS=true
ENV USE_STEALTH=true
ENV DEBIAN_FRONTEND=noninteractive

# Install system Chromium (most reliable method)
RUN apt-get update && apt-get install -y \
    chromium \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Verify browser installation and set path
RUN chromium --version && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome

# Set Chrome binary path for DrissionPage
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bulletproof_scraper.py .
COPY bulletproof_submitter.py .
COPY server.py .

# Create non-root user and set permissions
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.config/chromium && \
    chown -R appuser:appuser /home/appuser/.config

USER appuser

# Set Chrome flags for container environment
ENV CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding"

EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start server
CMD ["python", "server.py"]
