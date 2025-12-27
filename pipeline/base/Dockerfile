# Base Docker image for K-Pop pricing scrapers
# This image includes Chrome, ChromeDriver, and Python dependencies

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Chrome and ChromeDriver
# Note: Some packages removed as they're obsolete in Debian Trixie
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libfontconfig1 \
    libgbm1 \
    libgdk-pixbuf-2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    fonts-liberation \
    lsb-release \
    xdg-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
# Detect architecture and install appropriate Chrome version
RUN ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "amd64" ]; then \
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
        && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
        && apt-get update \
        && apt-get install -y google-chrome-stable \
        && rm -rf /var/lib/apt/lists/*; \
    elif [ "$ARCH" = "arm64" ]; then \
        echo "ARM64 detected - Installing Chromium (Chrome for ARM64 not available via apt)"; \
        apt-get update \
        && apt-get install -y chromium chromium-driver || apt-get install -y chromium \
        && ln -s /usr/bin/chromium /usr/bin/google-chrome || true \
        && if [ -f /usr/bin/chromedriver ]; then \
             ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver || true; \
           fi \
        && rm -rf /var/lib/apt/lists/*; \
    else \
        echo "Unsupported architecture: $ARCH"; \
        exit 1; \
    fi

# Install ChromeDriver
# Note: webdriver-manager (in requirements.txt) will handle version matching at runtime
# This pre-installation is optional but speeds up execution
# For ARM64, chromium-driver is installed above, for amd64 we try to pre-install
RUN ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "amd64" ]; then \
        CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) \
        && echo "Chrome major version: ${CHROME_VERSION}" \
        && CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}" 2>/dev/null || echo "") \
        && if [ -z "$CHROMEDRIVER_VERSION" ]; then \
             echo "Warning: Could not fetch ChromeDriver version, webdriver-manager will handle it at runtime"; \
           else \
             echo "Installing ChromeDriver ${CHROMEDRIVER_VERSION}"; \
             wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip 2>/dev/null || true; \
             if [ -f /tmp/chromedriver.zip ]; then \
               unzip -q /tmp/chromedriver.zip -d /tmp; \
               mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver 2>/dev/null || true; \
               chmod +x /usr/local/bin/chromedriver 2>/dev/null || true; \
               rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64; \
             fi; \
           fi; \
    elif [ "$ARCH" = "arm64" ]; then \
        echo "ARM64: ChromeDriver will be handled by webdriver-manager at runtime"; \
        echo "Note: Chromium on ARM64 works with webdriver-manager"; \
    fi

# Verify installations
RUN (google-chrome --version 2>/dev/null || chromium --version 2>/dev/null || echo "Warning: Chrome/Chromium not found") \
    && echo "ChromeDriver will be installed by webdriver-manager at runtime if needed"

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV DISPLAY=:99

# Create a non-root user (Cloud Run will use this)
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

# Default command (can be overridden)
CMD ["python", "--version"]

