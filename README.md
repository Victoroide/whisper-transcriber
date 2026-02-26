# Whisper Transcriber

> See [activate_env](activate_env) for virtual environment activation instructions on all platforms.

Desktop speech-to-text application powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) with a Go backend for system-level operations and a Python/CustomTkinter frontend.

## Architecture

The application uses a hybrid Go + Python design:

- **Go backend** (`core/`): Handles audio extraction via ffmpeg, hardware detection, IPC server, temp file management, and model download coordination.
- **Python frontend** (`ui/`): CustomTkinter GUI with faster-whisper inference, real-time transcription display, and multi-format export.

Communication between the two layers uses newline-delimited JSON over TCP (Windows) or Unix sockets.

## Prerequisites

- **Python 3.10+**
- **Go 1.22+** (for building the backend)
- **ffmpeg** installed and available on PATH

### Installing ffmpeg

- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add `bin/` to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` (Debian/Ubuntu) or equivalent

## Installation

### Development Setup

**Windows (PowerShell):**

```powershell
git clone https://github.com/Victoroide/whisper-transcriber.git
cd whisper-transcriber
.\scripts\install_dev.ps1
```

**Linux/macOS:**

```bash
git clone https://github.com/Victoroide/whisper-transcriber.git
cd whisper-transcriber
chmod +x scripts/install_dev.sh
./scripts/install_dev.sh
```

### Manual Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r ui/requirements.txt
pip install -r ui/requirements-dev.txt
```

## Usage

### Running in Development

```bash
python scripts/run.py
```

This automatically builds the Go backend if needed, then launches the UI.

### Running Without Go Backend

The application can run in standalone mode without the Go binary. Audio format conversion and hardware detection will not be available, but transcription works for WAV files directly:

```bash
python -m ui.app.main
```

### Building for Distribution

```bash
python scripts/build.py
```

Output is placed in `dist/WhisperTranscriber/`.

## Supported Formats

**Video**: .mp4, .avi, .mov, .mkv, .flv, .wmv, .webm

**Audio**: .mp3, .wav, .m4a, .ogg, .flac

## Model Sizes

| Model    | RAM Required | Speed    | Accuracy  |
| -------- | ------------ | -------- | --------- |
| tiny     | ~1 GB        | Fastest  | Basic     |
| base     | ~1 GB        | Fast     | Fair      |
| small    | ~2 GB        | Moderate | Good      |
| medium   | ~5 GB        | Slow     | Very Good |
| large-v3 | ~10 GB       | Slowest  | Best      |

The application auto-detects your hardware and recommends an appropriate model. Models are downloaded automatically on first use.

## Keyboard Shortcuts

| Shortcut | Action                       |
| -------- | ---------------------------- |
| Ctrl+O   | Open file browser            |
| Ctrl+S   | Save as .txt                 |
| Ctrl+C   | Copy transcript to clipboard |
| Esc      | Cancel transcription         |

## Export Formats

- **.txt** -- Plain text without timestamps
- **.srt** -- SubRip subtitle format
- **.vtt** -- WebVTT subtitle format
- **.json** -- Structured JSON with timestamps and full text

## Project Structure

```
whisper-transcriber/
├── core/               # Go backend
│   ├── cmd/wt-core/    # Entry point
│   ├── internal/       # Internal packages
│   │   ├── audio/      # ffmpeg wrapper
│   │   ├── cleanup/    # Temp file management
│   │   ├── hardware/   # GPU/CPU/RAM detection
│   │   ├── ipc/        # IPC server
│   │   └── models/     # Model downloader
│   └── Makefile
├── ui/                 # Python frontend
│   ├── app/
│   │   ├── components/ # UI widgets
│   │   ├── core/       # Business logic
│   │   └── utils/      # Helpers
│   └── requirements.txt
├── scripts/            # Build and dev scripts
├── tests/              # Test suites
└── .github/workflows/  # CI/CD
```

## Running Tests

**Go tests:**

```bash
cd core && go test ./...
```

**Python tests:**

```bash
python -m pytest tests/python/ -v
```

## License

See the repository for license information.
