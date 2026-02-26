# Concurrency Model

Whisper Transcriber relies entirely on a highly concurrent architecture to parallelize work across all logical cores of a user's machine, reducing extraction and transcription times exponentially compared to single-threaded solutions like vanilla `whisper` CLI.

## Go Backend: Worker Pools

### FFmpeg Extraction Bottleneck

A standard audio extraction command block (`ffmpeg -i input.mp4 -vn -c:a pcm_s16le output.wav`) is highly inefficient to run sequentially for large video files, such as a 2-hour lecture. FFmpeg relies heavily on single-thread I/O bottlenecks when extracting an entire track from complex containers (MKV, TS, etc.).

### Solution: Concurrent Workers

The Go core resolves this by dynamically launching a pool of `ffmpeg` instances.

1.  **Preparation Phase (`ffprobe`)**: The target media file is probed to determine its exact length in milliseconds. This is a lightweight call.
2.  **Job Enqueueing**: A `jobs <-chan int` channel is populated with segment start times. By default, the extractor divides the video into 30-second intervals (e.g., Job 1: 0s-30s. Job 2: 30s-60s).
3.  **Worker Pool Activation**: Go spins up a number of goroutines equivalent to the available system threads (`runtime.NumCPU() - 1`). Each worker repeatedly pulls a start time from the `jobs` channel, issues an `ffmpeg -ss [start] -t 30` slice request, saves a temporary `.wav`, and pushes the result path onto a `results chan Chunk`.
4.  **Ordering**: A specialized sequencer block intercepts the `results` channel. Because Worker 5 might finish processing a silent 30s chunk before Worker 2 finishes a complex noise segment, the Go sequencer catches out-of-order chunks and strictly transmits them across IPC in sequential 1-2-3-4-5 order.

## Python Frontend: Streaming Loop

At the application boundary, Python listens on a socket for incoming JSON notifications.

If Python processes JSON events directly within the same thread that handles the Graphical Interface (Tkinter) or runs Machine Learning Inference (`faster-whisper`), the app window will completely freeze. The concurrency model fixes this by keeping responsibilities strictly separated.

1.  **IPC Thread (`ui/app/core/ipc_client.py`)**: A permanent daemon thread exclusively reads lines from the socket. Since socket I/O can hang indefinitely, this thread does no processing; it strictly pushes raw dictionaries onto a `queue.Queue`.
2.  **UI Event Loop (`ui/app/window.py`)**: The `customtkinter` main loop spins at 60Hz. Every 100ms, it calls `.update()`, safely draining any pending chunks from the thread-safe `Queue` and mapping them to visual progress bars.
3.  \*\*Transcription Worker Thread`: Upon file submission, a dedicated thread is launched. This thread loops: waiting for chunks, running `transcribe()`, shifting segment timestamps mathematically based on the chunk index, and calling `self.after(0)` to paint the transcribed text back onto the UI loop.

This three-threaded architecture permits continuous, non-blocking UI rendering precisely while heavy GPU inference runs sequentially against the concurrent Go chunks.
