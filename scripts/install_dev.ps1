# Whisper Transcriber -- Windows Development Setup

Write-Host "Setting up Whisper Transcriber development environment..."

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
Write-Host "Installing Python dependencies..."
pip install -r ui\requirements.txt
pip install -r ui\requirements-dev.txt

# Verify Go installation
$goVersion = go version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Go found: $goVersion"
} else {
    Write-Host "WARNING: Go is not installed. Install Go 1.22+ from https://go.dev/dl/"
}

# Verify ffmpeg installation
$ffmpegVersion = ffmpeg -version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "ffmpeg found"
} else {
    Write-Host "WARNING: ffmpeg not found. Install from https://ffmpeg.org/download.html"
}

Write-Host ""
Write-Host "Setup complete. To run the application:"
Write-Host "  python scripts\run.py"
