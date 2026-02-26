# Model Cache (`ui/app/core/model_cache.py`)

The `ModelCache` singleton simplifies interactions with the `huggingface-hub` SDK and provides a unified interface for the frontend to determine if the user needs an internet connection prior to starting a transcription event.

## Core Component: ModelCache

### Initialization: `__init__()`

Instantiates the Python `Path` pointing strictly to the current user's operating system cache directory (`~/.cache/huggingface/hub/` on macOS/Linux and standard equivalents on Windows).

### `is_model_cached(model_size: str) -> bool`

This method protects the transcription engine from crashing gracefully when the device is entirely offline.

1.  **Format Construction**: HuggingFace formats model repository folders exclusively with a `models--` prefix. It dynamically constructs `models--Systran--faster-whisper-[size]`.
2.  **Validation**: A simple boolean check against the filesystem determines if the 1GB+ quantization blob (`.bin` or `.pt`) is currently available locally.

### `get_cache_dir() -> str`

Exposes the resolved string absolute path to the UI thread, primarily for debugging or for injecting as the target variable when invoking the Go `model-downloader` (if implemented).
