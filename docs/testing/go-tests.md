# Running Go Tests (`core/`)

The Core orchestrator is tested natively using the robust Golang `testing` internal package. These tests assert hardware abstractions, filesystem manipulation, and parallel extraction behaviors cleanly without requiring the Python frontend to exist.

## Test Categories

### Parallel Benchmark (`extractor_test.go`)

The `TestParallelExtraction` suite is the most computationally demanding verification in the repository.

- **Audio Prototyping**: Because pushing real 500MB media files to Github is blocked, this test uses `ffmpeg -f lavfi` to synthesize a 300-second pure white-noise file (`anoisesrc`) dynamically.
- **Assertion**: It sequentially processes this 300s file on a single thread and then iterates via the `ExtractChunks` worker pool, comparing total processing times.

### Connection Handlers (`server_test.go`)

- **Assertion**: Validates that launching `Server.Start()` properly opens localhost TCP ports or Unix Domain Sockets and writes `.sock` files effectively.

### Checksum Validation (`downloader_test.go`)

- **Assertion**: Writes random dummy binary strings to the disk, dynamically hashing them using `crypto/sha256` in real-time to assure the `VerifyChecksum` algorithm correctly throws errors if HuggingFace downloads corrupt.

## Running the Suite

Ensure you are located entirely within the `core/` subdirectory boundaries:

```bash
cd core
go test -v ./...
```

You should observe passes across all `core/internal/{audio,cleanup,hardware,ipc,models}` packages.
