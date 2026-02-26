#!/usr/bin/env bash
# Whisper Transcriber -- Unix Development Setup

set -e

echo "Setting up Whisper Transcriber development environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r ui/requirements.txt
pip install -r ui/requirements-dev.txt

# Verify Go installation
if command -v go &> /dev/null; then
    echo "Go found: $(go version)"
else
    echo "WARNING: Go is not installed. Install Go 1.22+ from https://go.dev/dl/"
fi

# Verify ffmpeg installation
if command -v ffmpeg &> /dev/null; then
    echo "ffmpeg found"
else
    echo "WARNING: ffmpeg not found. Install from your package manager or https://ffmpeg.org/"
fi

echo ""
echo "Setup complete. To run the application:"
echo "  python scripts/run.py"
