#!/bin/bash
# Install Playwright browsers for headless scraping

echo "Installing Playwright browsers..."

# Install playwright browsers
python -m playwright install chromium

# Install system dependencies (for Linux/Vercel)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing Linux dependencies..."
    # These are typically needed for headless Chrome on Linux
    apt-get update && apt-get install -y \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libasound2
fi

echo "Playwright installation complete!"