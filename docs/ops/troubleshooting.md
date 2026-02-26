# Whisper Transcriber: Complete Troubleshooting Guide

During normal operations, Whisper Transcriber spawns the Go core as a background process and connects over IPC. Failures to start, decode audio, or transcribe text fall into specific categorizations covered below.

## IPC Event Error Dictionary

The Go core emits standardized error JSON over the websocket in case of unrecoverable or retry-able errors.
Example JSON structure:

```json
{
  "type": "error",
  "data": {
    "code": "EXTRACTION_FAILED",
    "message": "ffprobe not found in PATH",
    "fatal": true
  }
}
```

### INVALID_COMMAND

- **Description:** The Python client transmitted an unrecognized string over the socket.
- **Resolution:** Verify that `ipc_client.send(command_name)` exclusively uses predefined tokens (`cancel`, `extract_audio`, `ping`, `hardware_check`). Ensure JSON encoding didn't mangle the string.

### HARDWARE_CHECK_FAILED

- **Description:** The Go core `DetectHardware()` function panicked while executing the `nvidia-smi` shell probe.
- **Resolution:** Confirm `nvidia-smi` exists within `C:\Windows\System32\` or the respective `$PATH` string. If the user machine strictly lacks a dedicated GPU, the application correctly ignores the fault and falls back strictly to the `device="cpu"` inference parameter.

### BINARY_NOT_FOUND

- **Description:** The Python layer failed to launch the binary stored at `ui/app/bin/wt-core.exe`.
- **Resolution:**
  1.  The Go binary has not been compiled natively for the developer's architecture. Run `go build -o ...` as detailed in `docs/ops/environment-setup.md`.
  2.  PyInstaller stripped the `bin/` payloads during compilation. Include the `--add-data` specification precisely.

### BIND_FAILED

- **Description:** The IPC Server failed to allocate the network port on Windows, or the UDS (Unix Domain Socket) on Linux/macOS.
- **Resolution:**
  1.  **Unix**: Delete the stale socket file located at `/tmp/wt-core-xxx.sock`. Ensure read/write file permissions exist on `/tmp`.
  2.  **Windows**: Another ghost iteration of the Go core (`wt-core.exe`) is running implicitly in the background. Abort it utilizing the Task Manager or `taskkill /IM wt-core.exe /f`.

### PATH_NOT_FOUND

- **Description:** The source video or audio file was deleted or the OS restricted access.
- **Resolution:** Disable restrictive active-scanning antivirus software which frequently locks incoming media files while isolating potential threats.

### INVALID_FORMAT

- **Description:** FFprobe failed to parse the header of the dropped file indicating corrupted MP4 headers or an intrinsically invalid codec structure.
- **Resolution:** Utilize Handbrake or Adobe Media Encoder to normalize the target input video format. Alternatively, attempt dragging an explicit `.wav` extract.

### EXTRACTION_FAILED

- **Description:** The core worker pool failed to extract one of the consecutive 30-second segments off the video file via `ffmpeg`.
- **Resolution:** FFmpeg is not installed securely on the System. Append the location of the binary folder specifically mapping to your User Path variables in the Advanced System Settings dialog.

## Python Frontend Common Issues

### Faster-Whisper Model Fails to Load

If downloading the offline models from huggingface fails:

1.  **Network Drop:** HuggingFace repository servers may be currently offline or rate limiting the target IP address.
2.  **Cache Corruption:** Delete the cache. Whisper transcriber models (`tiny`, `small`, `base`, `large-v3`) usually download into `C:\Users\Username\.cache\huggingface\hub\`. Delete the `models--Systran--faster-whisper-tiny` directory and restart the App to reinitialize generation.

### Complete UI Lockup or Frozen Window

If CustomTkinter entirely stops rendering the progress bar or allowing clicks:

1.  **Fatal Logic:** Identify if the transcriber thread is inappropriately executing `transcribe()` synchronously upon the main loop block.
2.  **Socket Spin:** Ensure `IPCClient` polling functions strictly use `timeout=0.2`.

### Error: audio is too short to transcribe

This non-fatal exception emerges when a synthetic audio subset happens to include 15-30 seconds of absolute zeroes or silence padding causing `faster_whisper.transcribe()` to error out. To prevent disruption, the UI handles it cleanly and ignores these localized chunks mathematically. Ensure `vad_filter=False` exists within the transcribe parameter structure to accommodate synthetic tests safely.
