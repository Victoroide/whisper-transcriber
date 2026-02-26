# Environment Setup

Welcome to the Whisper Transcriber repository. The following steps outline how to deploy the full environment for local development and build testing on modern Windows, Linux, or macOS systems.

## Prerequisites

### 1. Python 3.10 or higher

Ensure that `python --version` returns an acceptable version. Virtual environments are highly recommended.

### 2. Go 1.21 or higher

Ensure that `go version` succeeds. The back-end orchestrator explicitly requires the official Golang toolchain for building the executable binaries prior to Pyinstaller packaging.

### 3. FFmpeg and FFprobe

The Go back-end invokes `ffmpeg` directly from the OS shell environments via `os/exec`.

- **Windows:** Download a compiled Windows build from [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or scoop (`scoop install ffmpeg`). Place the `bin/` directory on your User or System `PATH` variable.
- **macOS:** Install via Homebrew: `brew install ffmpeg`
- **Linux (Debian):** Install via Apt: `sudo apt install ffmpeg`

Verify availability by running:

```bash
ffmpeg -version
ffprobe -version
```

### 4. GPU Acceleration (CUDA - Optional)

To enable the highest performance inference scaling in the Python `faster-whisper` backend on Windows/Linux environments, you **must** install the NVIDIA drivers and CUDA Toolkit libraries. Use `nvidia-smi` to probe your existing CUDA setup. The current dependencies require cuDNN specifically matched to CUDA 11 or 12.

If you don't possess a compatible GPU (or run on macOS), the engine gracefully falls back to system RAM/CPU processing at significant runtime penalty.

## Installation Workflow

Follow these chronological steps from an empty terminal:

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/Victoroide/whisper-transcriber.git
    cd whisper-transcriber
    ```

2.  **Establish Virtual Environment**
    Create your Python enclosed environment:

    ```bash
    # Windows PowerShell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # Unix/Git Bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Python Dependencies**
    By default, PyTorch attempts to leverage CUDA:

    ```bash
    pip install -U pip
    pip install -r ui/requirements.txt
    ```

4.  **Compile the Go Core**
    You must generate the IPC core server in the appropriate expected frontend location `ui/app/bin/`.

    ```bash
    # On Windows:
    cd core
    go build -o ../ui/app/bin/wt-core.exe ./cmd/wt-core/
    cd ..

    # On macOS/Linux:
    cd core
    go build -o ../ui/app/bin/wt-core ./cmd/wt-core/
    cd ..
    ```

## Development and Testing

Begin running the integration and component test suites to certify environment integrity:

- **Go Test Coverage:**
  `cd core && go test -v ./...`
- **Python Test Coverage:**
  `cd whisper-transcriber && pytest tests/python/`

You can manually trigger the UI process to ensure everything executes directly from source files using: `python run.py`. It should display a connected status flag in the bottom-right corner.
