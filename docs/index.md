# System Overview

Whisper Transcriber is a high-performance audio transcription desktop application combining a Go core and a Python CustomTkinter frontend. It processes video and audio using faster-whisper and delivers results significantly faster than monolithic approaches by leveraging CPU worker pools and real-time IPC streaming.

## Documentation Map

If you are a new contributor, please read the documentation in the following order:

### 1. Architecture

- [Architecture Overview](architecture/overview.md) - The Go/Python split and high-level design.
- [Concurrency Model](architecture/concurrency-model.md) - How Go worker pools and Python threads synchronize.
- [IPC Protocol](architecture/ipc-protocol.md) - The JSON messaging schema used over the Unix/TCP socket.

### 2. Operations & Setup

- [Environment Setup](ops/environment-setup.md) - How to configure your Python `.venv` and install Go.
- [Building Deployments](ops/building.md) - How to compile the Go binary and package the app with PyInstaller.
- [Troubleshooting](ops/troubleshooting.md) - Mapping of IPC error codes to common environment failures.

### 3. Backend (Go)

- [Audio Extractor](go/audio-extractor.md) - The core parallel chunk logic.
- [Model Downloader](go/model-downloader.md) - Fetching the `tiny` model locally.
- [Hardware Detector](go/hardware-detector.md) - Probing the system for CUDA GPUs.
- [IPC Server](go/ipc-server.md) - The connection handler.
- [Temp Cleanup](go/temp-cleanup.md) - Lifecycle management of extracted WAV chunks.

### 4. Frontend (Python)

- [Transcription Engine](python/transcription-engine.md) - Integration with `faster-whisper`.
- [Text Processing](python/text-processing.md) - Sanitization of Whisper output.
- [Export Formats](python/export-formats.md) - Generation of SRT, VTT, and standard Text files.
- [IPC Client](python/ipc-client.md) - The socket reading thread block.
- [Model Cache](python/model-cache.md) - Validating local model caches.

### 5. Frontend (UI)

- [Window Layout](ui/window-layout.md) - The hierarchy of CustomTkinter widgets.
- [Threading Model](ui/threading-model.md) - Separation of the main loop and background workers.
- [Component Lifecycle](ui/component-lifecycle.md) - Initialization and teardown events.

### 6. Testing

- [Python Tests](testing/python-tests.md) / [Go Tests](testing/go-tests.md) - Current suite coverage.
- [Adding Tests](testing/adding-tests.md) - Guidelines for new implementations.
