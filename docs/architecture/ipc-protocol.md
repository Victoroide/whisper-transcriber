# IPC Protocol (`core/internal/ipc/messages.go`)

The Inter-Process Communication (IPC) string syntax is exclusively built upon plain JSON text encapsulated by newline returns (`\n`).

Because Go structs strictly serialize, all fields align perfectly with Python dict mappings.

## Message Format Rule

Every single message injected across the socket, whether initiated by the GUI client or by the Go core daemon, must strictly conform to this envelope structure:

```json
{
  "type": "string",
  "data": { ... } // Optional nested objects mapped directly to the event context.
}
```

## Python -> Go (Requests)

The Tkinter Interface sends commands to instruct the Go background orchestrator.

### 1. `ping`

A heartbeat validator used by Python upon application startup. Returns a generic acknowledgment.

- **Payload**: `{"type": "ping"}`

### 2. `hardware_check`

Fired securely at boot to probe the user OS for CUDA dependencies (`nvidia-smi`).

- **Payload**: `{"type": "hardware_check"}`
- **Go Response**: A boolean wrapper signaling `{"HasGPU": true, "HasCUDA": true, "Devices": ["NVIDIA GeForce RTX 3060"]}` natively.

### 3. `extract_audio`

Kicks off the `AudioExtractor` parallel worker pool, explicitly passing user specifications from the UI variables.

- **Payload**:

```json
{
  "type": "extract_audio",
  "data": {
    "file_path": "C:\\videos\\interview.mp4",
    "chunk_duration": 30.0
  }
}
```

### 4. `cancel`

Intercepts the cancellation button click, aborting any active extraction context immediately.

- **Payload**: `{"type": "cancel"}`

## Go -> Python (Events/Responses)

The background server utilizes these definitions to update the Tkinter main loop seamlessly.

### 1. `pong`

- **Response to**: `ping` request.

### 2. `hardware_info`

- **Response to**: `hardware_check` probing. Yields the specific list of GPU adapters available.

### 3. `extraction_progress`

Broadcast dynamically during heavy `.wav` generation workloads updating the UI mathematical progress bars natively.

- **Payload**:

```json
{
  "type": "extraction_progress",
  "data": {
    "percentage": 42.5
  }
}
```

### 4. `audio_chunk`

Streams sequentially exactly as a 30-second chunk exits the ffmpeg worker pool securely.

- **Payload**:

```json
{
  "type": "audio_chunk",
  "data": {
    "index": 1,
    "start_time": 30.0,
    "path": "C:\\temp\\wt-core-x\\chunk_001.wav"
  }
}
```

### 5. `audio_extraction_complete`

Broadcasts implicitly when the source file has been exhausted entirely. Maps the sum total expected.

- **Payload**: `{"total_chunks": 5}`

### 6. `error`

Resolves unrecoverable dependencies directly into user-facing warnings on the GUI string format.

- **Payload**:

```json
{
  "type": "error",
  "data": {
    "code": "EXTRACTION_FAILED",
    "message": "ffmpeg not found in PATH",
    "fatal": true
  }
}
```

- **\*Note:** All IPC Error codes mapped to the `error` signal are exhaustively documented in `[Troubleshooting](../ops/troubleshooting.md)`.\*
