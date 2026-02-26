# IPC Server (`core/internal/ipc/server.go`)

The central nervous system of the Go back-end, handling the transport layer for real-time JSON strings traversing sockets.

## Core Component: Server

### `NewServer(...)`

Bootstraps the Unix Domain Socket (macOS/Linux `/tmp/*.sock`) or raw TCP loopback listener (`127.0.0.1:0` on Windows). Generates random assignment variables to prevent collision between separate parallel executions of the Transcriber.

### `Start()`

Forks the `handleConnection` routine blocking strictly for a single arbitrary connection from the Python client. Rejects consecutive connection attempts arbitrarily. This acts as a security safeguard ensuring only the parent launcher application intercepts transcripts.

### `Send(msgType string, data map[string]interface{})`

Crucial real-time streamer module. Takes standardized Go dictionary mappings, serializes them natively via `json.Marshal`, formats exactly with a trailing newline `\n`, and propagates to Python.

- **Buffer Flushes**: Resolves OS internal TCP buffering latencies by explicitly requiring a `writer.Flush()` invocation upon the `bufio` wrapper.

## Incoming Protocol Mappings

- `extract_audio`: Kicks off the `audio.Extractor` worker pool.
- `cancel`: Aborts context triggers globally, halting FFmpeg workers mid-flight and commanding the `cleanup` package to purge temp fragments securely.
- `hardware_check`: Immediately interrogates CUDA availability via shell requests (`nvidia-smi`). Validations return `hardware_info`.
