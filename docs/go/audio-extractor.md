# Audio Extractor (`core/internal/audio/extractor.go`)

The `AudioExtractor` struct provides operations to invoke FFmpeg and divide media tracks into raw audio slices for maximum performance.

## Structure and Responsibilities

- `ExtractChunks(inputPath string, outputDir string, chunkDurationSeconds float64, progress chan<- AudioProgress) (<-chan Chunk, error)`
  The principal function exported to the main IPC worker. It coordinates calculating the true millisecond duration, generating the expected sequence count of output `*.wav` chunks, and launching a thread pool.

### How it Works

1.  **Preparation**: Runs `ProbeDuration` iteratively to get precise file bounds without reading binary bytes natively.
2.  **Worker Pool**: Determines how many CPU cores `runtime.NumCPU()` function resolves. Starts exactly that many goroutines, listening eagerly on a `jobs` buffered channel.
3.  **Command Execution**: Builds and triggers `ffmpeg.exe` to decode segments synchronously. `ffmpeg -ss [start] -t [length] -i [input] -c:a pcm_s16le -ar 16000 -ac 1 output.wav`.
4.  **Sequencing**: Submits the generated chunks over the outgoing `<-chan Chunk` channel explicitly in ascending sequence so that the Python decoder maintains the original conversation sequence linearly.

## Error Handling

Failures of `exec.Command` return an explicit `fmt.Errorf` detailing the original ffmpeg standard-error message cleanly over the socket via the error IPC package.
