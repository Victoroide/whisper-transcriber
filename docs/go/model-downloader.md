# Model Downloader (`core/internal/models/downloader.go`)

The `Downloader` struct handles fetching large binary model files (such as Hugging Face `ggml` models) securely and reliably. It is designed to be robust against network interruptions.

## Primary Component: `Downloader`

### Initialization: `NewDownloader(cacheDir string)`

Creates a new downloader instance targeting a specific cache directory. It guarantees that the directory tree exists via `os.MkdirAll`.

### Core Method: `Download(...)`

```go
func (d *Downloader) Download(
	url string,
	filename string,
	expectedSHA256 string,
	progress DownloadProgressFunc,
) (string, error)
```

This is the workhorse of the package, featuring several resilience mechanisms:

1.  **Checksum Verification**: Before initiating any network requests, it checks if `filename` already exists in `cacheDir`. If it does, and `expectedSHA256` is provided, it validates the existing file. If valid, the download is skipped entirely.
2.  **Resumable Downloads**: The downloader uses HTTP Range requests (`Range: bytes=X-`) to resume interrupted downloads. It looks for a `.part` file and checks its size to determine the starting byte.
3.  **Progress Tracking**: It accepts a `DownloadProgressFunc` callback, allowing the caller to receive real-time updates on downloaded bytes versus total bytes, enabling accurate progress bars in the UI.
4.  **Security via `.part` Files**: Downloads are initially written to a temporary `.part` file. Only after the download completes and the SHA256 checksum (if provided) is exclusively validated is the file atomically renamed to its final target `filename`. If the checksum fails, the corrupt `.part` file is deleted.

## Supported Callbacks

```go
type DownloadProgressFunc func(downloaded, total int64)
```

This signature is used to bridge the Go back-end progress directly to the IPC Server, which then transmits `download_progress` percentages over the socket to Python.
